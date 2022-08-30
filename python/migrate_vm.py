#!/usr/bin/env python

“”“
This VM Migration code is suit for NFS storage
This is not live migration (Live migration must inclde copy memory step)
Migration steps incldes migrate disk, deactivate disk, create new image for vm
”“”


import rhvm_api

# connect to rhvm api
def connect(api_url, user, password):
    VERSION = params.Version(major='4', minor='5')
    rhvm_api = API(url=api_url, user=rhv_username, password=rhv_password, insecure=True)
    return rhvm_api

# prepare to migration vm
def get_vms_to_migrate(rhvm_api, search_query):
    vms_to_migrate = []
    for vm in rhvm_api.vms.list(query=search_query):
        print("'{}' is set to be migrated.".format(vm.name))
        vms_to_migrate.append(vm)
    return vms_to_migrate

# start to migrate vm disks
def migrate_disks(rhvm_api, vms_to_migrate, old_storage_id, new_storage_id, nfs_mount_dir, migrate_tag):
    completed_vms = []
    failed_vms = []
    for vm in vms_to_migrate:
        print("Starting migration for '{}'.".format(vm.name))
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


# start deactivate vm disk
def deactivate_disk(vm, disk):
    print("[{}] Deactivating '{}' for migration...".format(vm.name, disk.name))
    if disk.active:
        disk.deactivate()
        while not disk.active:
            time.sleep(3)

#create new disk in nfs storage
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

# find new image path
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

# set vm boot order
def set_boot_order(vm):
    vm.set_os(params.OperatingSystem(boot=[params.Boot(dev='hd')]))
    vm.update()

# check vm status
def check_vm(vm, old_storage_id):
    disks = vm.disks.list()
    for disk in disks:
        for storage_domain in disk.storage_domains.storage_domain:
            if storage_domain.id == old_storage_id:
                return False
    return True

# remove vm tag
def remove_tag(vm, completed_vms, migrate_tag):
    completed_vms.append(vm.name)
    for tag in vm.tags.list():
        if tag.name == migrate_tag:
            tag.delete()

# print error message
def error_message(vm, disk, failed_vms):
    failed_vms.append("{} ({})".format(vm.name, disk.name))
    print("[{}] ERROR: Could not migrate '{}'. Reactivating original disk. "
          "Please manually clean up any remnants from this failed migration.".format(vm.name, disk.name))
    disk.activate()


    api_url = "https://{rhevm_fqdn}/ovirt-engine/api/{item}"
    user = ''
    password = ''


    old_storage_id = ''
    new_storage_id = ''
    nfs_mount_dir = ''
    migrate_tag = 'Migrate_to_NFS'
    search_query = 'Storage.name= Status=down Tag={}'.format(migrate_tag)

   
    rhvm_api = connect(api_url, user, password)
    vms_to_migrate = get_vms_to_migrate(rhvm_api, search_query)
    completed_vms, failed_vms = migrate_disks(rhvm_api, vms_to_migrate, old_storage_id, new_storage_id, nfs_mount_dir,
                                              migrate_tag)
    print("No more VMs to migrate.")
    os.remove('.rhv_migration_lock')
