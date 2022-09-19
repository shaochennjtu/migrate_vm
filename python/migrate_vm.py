“”“
Static Migration:
This VM Migration code is suit for NFS storage(Shared Storage)
This is not live migration (Live migration must inclde copy memory step)
Make sure Migrate VMs are on Powerdown or Pause status.
”“”

import os
import time
import logging
from ..helpers import rhvm_api

log = logging.getLogger('migrate')

old_storage_id = ''
new_storage_id = ''
nfs_mount_dir = ''
search_query = ''


class Migration(object):
    """"""

    # start deactivate vm disk
    def deactivate_disk(vm, disk):
        print("[{}] Deactivating '{}' for migration...".format(vm.name, disk.name))
        if disk.active:
            disk.deactivate()
            while not disk.active:
                time.sleep(3)


    # create new image for VM
    def create_nfs_disk(rhvm_api, new_storage_id, disk, vm):
        print("[{}] Creating an NFS disk for '{}'...".format(vm.name, disk.name))
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


    # set new image path for VM
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


    # attach/detach vm disk
    def attach_detach_disk(vm, disk, new_disk):
        print("[{}] Attaching the '{}' NFS volume to the VM...".format(vm.name, disk.name))
        vm.disks.add(params.Disk(id=new_disk.id, active=True))
        print("[{}] Detaching the '{}' NFS volume from the VM...".format(vm.name, disk.name))
        disk.delete(action=params.Action(detach=True))


    # print error message
    def error_message(vm, disk, failed_vms):
        failed_vms.append("{} ({})".format(vm.name, disk.name))
        print("[{}] ERROR: Could not migrate '{}'. Reactivating original disk. "
              "Please manually clean up any remnants from this failed migration.".format(vm.name, disk.name))
        disk.activate()


    # start to migrate vm disks
    def migrate_disks(rhvm_api, old_storage_id, new_storage_id, nfs_mount_dir):
        completed_vms = []
        failed_vms = []
        if storage_domain.id == old_storage_id:     #Judge whether the new storage are same with old storage, will not move if same.
            print("[{}] '{}' needs to be migrated...".format(vm.name, disk.name))
            try:
                deactivate_disk(vm, disk)
                print("[{}] Deactivating disk '{}' for migration...".format(vm.name, disk.name))
                new_disk = create_nfs_disk(rhvm_api, new_storage_id, disk, vm)
                print("[{}] Creating an NFS disk for '{}'...".format(vm.name, disk.name))
                image_path = find_image(new_storage_id, new_disk, nfs_mount_dir)
                if image_path:
                    if os.system("qemu-img convert -f qcow -O raw nfs:{}/volume-{}:id={}:conf={} {}".format(
                        image_path)) == 0:
                        attach_detach_disk(vm, disk, new_disk)
                        print("[{}] Sucessfully migrated '{}'!".format(vm.name, disk.name))
                    else:
                        error_message(vm, disk, failed_vms)
                else:
                    error_message(vm, disk, failed_vms)
            except:
                error_message(vm, disk, failed_vms)
        return completed_vms, failed_vms


    print("No more VMs to migrate.")
    os.remove('.rhv_migration_lock')

