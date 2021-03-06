#!/usr/bin/env python

# RHV Storage Migration with NFS storage

import logging
import requests
import os
import time
import re
from fabric.api import settings, run
from ..helpers import CheckComm
from ..helpers.rhvm_api import RhevmAction
from check_points import CheckPoints

log = logging.getLogger('bender')


def _get_nfs_info(self):
    log.info("Getting NFS storage informations...")

    self._nfs_ip = CONST.NFS_INFO.get("ip")
    self._nfs_pass = CONST.NFS_INFO.get("password")
    self._nfs_data_path = CONST.NFS_INFO.get("data_path")
    log.info("Getting NFS finished.")

    
def _get_disk_size(self):
    log.info("Getting disk size...")
    self._disk_size = CONST.DISK_INFO.get("size")
    log.info("Getting disk size finished.")

#Create VMs, attach disk to VMs
def _create_vm(self, vm_name, cluster_name):
    log.info("Creating VM %s", vm_name)
    self._rhvm.create_vm(vm_name=vm_name, cluster_name=cluster_name)
    time.sleep(30)

        
#Create a float disk for vm using
def _create_float_disk(self, disk_name):
    log.info("Creating a float disk for VM")
        
    disk_type = "nfs"
    sd_name = self._sd_name

    if disk_type == "localfs" or disk_type == "nfs":
        disk_size = self._disk_size
        self._rhvm.create_float_image_disk(sd_name, disk_name, disk_size)
        
    time.sleep(60)

    
def _attach_disk_to_vm(self, vm_name, disk_name):
    log.info("Attaching the float disk to VM %s", vm_name)
    bootable = True
    self._rhvm.attach_disk_to_vm(disk_name, vm_name, bootable=bootable)
    time.sleep(30)

    
def _create_vms_with_disk(self,vm_quantity=1):
    log.info("Creating VMs with disk...")
    try:
        cluster_name = self._cluster_name

        value = 1
        while value <= vm_quantity:
            vm_name = self._vm_name + '_vm' + str(value)
            disk_name = vm_name + '_Disk1'
                
            # Create the vm
            self._create_vm(vm_name, cluster_name)
                
            # Get disk info
            self._get_disk_size()

            # Create the float disk
            self._create_float_disk(disk_name)

            # Attach the disk to vm
            self._attach_disk_to_vm(vm_name, disk_name)

            value += 1

    except Exception as e:
        log.exception(e)
        return False
    return True


#Operations on VM
def _wait_vm_status(self, vm_name, expect_status):
    log.info("Waitting the VM to status %s" % expect_status)
    i = 0
    vm_status = "unknown"
    while True:
        if i > 30:
            log.error("VM status is %s, not %s" % (vm_status, expect_status))
            return False
        vm_status = self._rhvm.list_vm(vm_name)['status']
        log.info("The VM status is: %s" % vm_status)
        if vm_status == expect_status:
            return True
        time.sleep(10)
        i += 1


def _start_vm(self, vm_name):
    log.info("Start up the VM %s" % vm_name)

    try:
        self._rhvm.operate_vm(vm_name, 'start')
        time.sleep(60)

        # Wait the vm is up
        self._wait_vm_status(vm_name, 'up')

    except Exception as e:
        log.exception(e)
        return False

    log.info("Start VM %s finished.", vm_name)
    return True


def connect(rhvm_api_url, rhv_username, rhv_password):
    VERSION = params.Version(major='4', minor='0')
    rhvm_api = API(url=rhvm_api_url, username=rhv_username, password=rhv_password, insecure=True)

    return rhvm_api


def get_vms_to_migrate(rhvm_api, search_query):
    vms_to_migrate = []
    for vm in rhvm_api.vms.list(query=search_query):
        print("'{}' is set to be migrated.".format(vm.name))
        vms_to_migrate.append(vm)
    return vms_to_migrate


def migrate_disks(rhvm_api, vms_to_migrate, old_storage_id, new_storage_id, nfs_mount_dir, migrate_tag):
    completed_vms = []
    failed_vms = []
    for vm in vms_to_migrate:
        print("Starting migration for '{}'.".format(vm.name))
        remove_snapshots(vm)
        print("[{}] Checking for disks to migrate...".format(vm.name))
        disks = vm.disks.list()
        for disk in disks:
            for storage_domain in disk.storage_domains.storage_domain:
                if storage_domain.id == old_storage_id:
                    print("[{}] '{}' needs to be migrated...".format(vm.name, disk.name))
                    try:
                        deactivate_disk(vm, disk)
                        print("[{}] Attempting to migrate '{}' to NFS...".format(vm.name, disk.name))
                        new_disk = create_nfs_disk(rhvm_api, new_storage_id, disk, vm)
                        print("[{}] Converting '{}' from RBD to NFS...".format(vm.name, disk.name))
                        image_path = find_image(new_storage_id, new_disk, nfs_mount_dir)
                        if image_path:
                            if os.system("qemu-img convert -p -O raw rbd:{}/volume-{}:id={}:conf={} {}".format(image_path)) == 0:
                                attach_detach_disk(vm, disk, new_disk)
                                set_boot_order(vm)
                                print("[{}] Sucessfully migrated '{}'!".format(vm.name, disk.name))
                            else:
                                print("[{}] Failed to convert '{}' from RBD to NFS.".format(vm.name, disk.name))
                                error_message(vm, disk, failed_vms)

                        else:
                            print("[{}] Could not find the correct image file to convert.".format(vm.name))
                            error_message(vm, disk, failed_vms)
                    except:
                        error_message(vm, disk, failed_vms)
        done = check_vm(vm, old_storage_id)
        if done:
            remove_tag(vm, completed_vms, migrate_tag)
    return completed_vms, failed_vms


def remove_snapshots(vm):
    print("[{}] Checking VM for snapshots...".format(vm.name))
    snapshots = vm.snapshots.list()
    if len(snapshots) > 1:
        removed_snaps = 0
        for snapshot in snapshots:
            if snapshot.description != 'Active VM' and snapshot.description != 'Active VM snapshot':
                print("[{}] Removing snapshot '{}'...".format(vm.name, snapshot.description))
                snapshot.delete()
                removed_snaps += 1
                new_snapshots = vm.snapshots.list()
                while len(new_snapshots) > len(snapshots) - removed_snaps:
                    time.sleep(3)
                    new_snapshots = vm.snapshots.list()


def deactivate_disk(vm, disk):
    print("[{}] Deactivating '{}' for migration...".format(vm.name, disk.name))
    if disk.active:
        disk.deactivate()
        while not disk.active:
            time.sleep(3)


def create_nfs_disk(rhvm_api, new_storage_id, disk, vm):
    print("[{}] Creating an NFS image for '{}'...".format(vm.name, disk.name))
    new_storage_domain = rhvm_api.storagedomains.get(id=new_storage_id)
    disk_params = params.Disk()
    disk_params.set_alias(disk.name)
    disk_params.set_size(disk.size)
    disk_params.set_interface('virtio')
    disk_params.set_format('raw')
    new_disk = new_storage_domain.disks.add(disk_params)
    while new_disk.status.state != 'ok':
        new_disk = new_storage_domain.disks.get(id=new_disk.id)
        time.sleep(3)
    return new_disk


def find_image(new_storage_id, new_disk, nfs_mount_dir):
    image_path = "{}/{}/images/{}/".format(nfs_mount_dir, new_storage_id, new_disk.id)
    image_dir_files = os.listdir(image_path)
    if len(image_dir_files) == 3:
        for filename in image_dir_files:
            if '.meta' in filename or '.lease' in filename:
                pass
            else:
                image_path += filename
                return image_path
    return False


def attach_detach_disk(vm, disk, new_disk):
    print("[{}] Attaching the '{}' Cinder volume to the VM...".format(vm.name, disk.name))
    vm.disks.add(params.Disk(id=new_disk.id, active=True))
    print("[{}] Detaching the '{}' NFS volume from the VM...".format(vm.name, disk.name))
    disk.delete(action=params.Action(detach=True))


def set_boot_order(vm):
    vm.set_os(params.OperatingSystem(boot=[params.Boot(dev='hd')]))
    vm.update()


def check_vm(vm, old_storage_id):
    disks = vm.disks.list()
    for disk in disks:
        for storage_domain in disk.storage_domains.storage_domain:
            if storage_domain.id == old_storage_id:
                return False
    return True


def remove_tag(vm, completed_vms, migrate_tag):
    completed_vms.append(vm.name)
    for tag in vm.tags.list():
        if tag.name == migrate_tag:
            tag.delete()


def error_message(vm, disk, failed_vms):
    failed_vms.append("{} ({})".format(vm.name, disk.name))
    print("[{}] ERROR: Could not migrate '{}'. Reactivating original disk. "
          "Please manually clean up any remnants from this failed migration.".format(vm.name, disk.name))
    disk.activate()


    rhvm_api_url = 'https://{rhevm_fqdn}/ovirt-engine/api/{item}'
    rhv_username = ''
    rhv_password = ''


    old_storage_id = ''
    new_storage_id = ''
    nfs_mount_dir = ''
    migrate_tag = 'Migrate_to_NFS'
    search_query = 'Storage.name= Status=down Tag={}'.format(migrate_tag)

   
    rhvm_api = connect(rhvm_api_url, rhv_username, rhv_password)
    vms_to_migrate = get_vms_to_migrate(rhvm_api, search_query)
    completed_vms, failed_vms = migrate_disks(rhvm_api, vms_to_migrate, old_storage_id, new_storage_id, nfs_mount_dir,
                                              migrate_tag)
    print("No more VMs to migrate.")
    os.remove('.rhv_migration_lock')
