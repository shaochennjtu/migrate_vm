# Migrate virtual machines from one host to another in the RHV environment.

Live migration provides the ability to move a running virtual machine between physical hosts with no interruption to service. The virtual machine’s RAM is copied from the source host to the destination host. Storage and network connectivity are not altered.

# RHVM moves the following contents of the virtual machine from the original host machine to the destination. 
  - Memory
  - Storage
  - Network connectivity 


For live migration to work properly, the new host must have a CPU with the same architecture and features as the original host. 

# Live migration of virtual machines requires the following configuration prerequisites:
  - The virtual machine must be migrated to a host in the same cluster as the host where the virtual machine is running. The status of both hosts must be Up.
  - Both hosts must have access to the same virtual networks, VLANs, and data storage domains.
  - The destination host must have enough CPU capacity and RAM to support the virtual machine’s requirements.

# Live migration is performed using the migration network. 
The default configuration uses the ovirtmgmt network as both the management network and the migration network. 
