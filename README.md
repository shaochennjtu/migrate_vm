# Ansible  - Playbook to migrate vms to migrate cross-cluster

Playbook was created to migrate vm between RHV Clusters.


## Usage
Usage
  - Create ansible variables file vars/rhv.yml, with your RHV Engine information. it is recommended create a [ansible-vault](https://docs.ansible.com/ansible/latest/user_guide/playbooks_vault.html) file
```
    Make sure all the required software is installed.
    git clone repository
    Create ansible variables file vars/rhv.yml, with your RHV Engine information. it is recommended create a ansible-vault file

    rhv_api: "https://vm-198-206.lab.eng.pek2.redhat.com "
    rhv_user: "admin@internal"
    rhv_pass: "password"

    Run playbook as follows:
    $ ansible-playbook migrate_vm.yml --ask-vault -e "vms_to_migrate=HostedEngine" -e "cluster_migrate_to=Cluster" -e "host_migrate_to=cshaovm1"
    $ ansible-playbook migrate_vm.yml --ask-vault -e "vms_to_migrate=HostedEngine" -e "cluster_migrate_to=L1"

Arguments:

    vms_to_migrate: vm to migrate
    
    cluster_migrate_to: cluster where you want to migrate vm
    
    host_migrate_to: host where you want to migrate vm (host from another cluster)
    
