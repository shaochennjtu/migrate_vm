# Ansible  - Playbook to migrate vms to migrate cross-cluster

Playbook was created to migrate vm between RHV Clusters.


## Usage
  - Create ansible variables file vars/rhv.yml, with your RHV Engine information. it is recommended create a [ansible-vault](https://docs.ansible.com/ansible/latest/user_guide/playbooks_vault.html) file
```
---
rhv_api: "https://bootp-xx-xx-xx.lab.eng.pek2.redhat.com/ovirt-engine/ "
rhv_user: "admin@internal"
rhv_pass: "password"
```

## Running the Playbook
To run the playbook, execute the ansible-playbook command as follows:
```
    $ ansible-playbook migrate_vm.yml --ask-vault -e "vms_to_migrate=cshaovm01" -e "cluster_migrate_to=Cluster" -e "host_migrate_to=cshaohost1"
    $ ansible-playbook migrate_vm.yml --ask-vault -e "vms_to_migrate=cshaovm01" -e "cluster_migrate_to=L1"

```


Arguments:
- vms_to_migrate: vm to migrate
- cluster_migrate_to: cluster where you want to migrate vm
- host_migrate_to: host where you want to migrate vm (host from another cluster)

