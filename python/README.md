# Migrate virtual machines from one host to another in the RHV environment.

Live migration is useful to support maintenance tasks on hosts without disrupting your running virtual machines.
Live migration refers to the process of moving a virtual machine from one physical host to another while it is running. 

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
