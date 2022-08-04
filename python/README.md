# Migrate virtual machines from one host to another in the RHV environment.

Live migration is useful to support maintenance tasks on hosts without disrupting your running virtual machines.
Live migration refers to the process of moving a virtual machine from one physical host to another while it is running. 
RHVM moves the following contents of the virtual machine from the original host machine to the destination. 
  - Memory
  - Storage
  - Network connectivity 


For live migration to work properly, the new host must have a CPU with the same architecture and features as the original host. Red Hat Virtualization helps you manage this by organizing hosts into clusters. A virtual machine may only migrate to hypervisor hosts that are members of its cluster. This helps you ensure that virtual machines do not migrate between machines that support a different set of processor features.


Administrators must ensure that their Red Hat Virtualization environment is correctly configured to support live migration in advance of using it. Live migration of virtual machines requires the following configuration prerequisites:

  - The virtual machine must be migrated to a host in the same cluster as the host where the virtual machine is running. The status of both hosts must be Up.
  - Both hosts must have access to the same virtual networks, VLANs, and data storage domains.
  - The destination host must have enough CPU capacity and RAM to support the virtual machine’s requirements.
  - The virtual machine must not have the cache!=none custom property set. The cache parameter configures the different cache modes for a virtual machine. Live migration requires a disabled virtual machine cache to ensure a coherent virtual machine migration.

Live migration is performed using the migration network. The default configuration uses the ovirtmgmt network as both the management network and the migration network. Although each live migration is limited to a maximum transfer speed, and there are a maximum number of migrations that may run concurrently, concurrent live migrations can saturate a network shared by management and migration traffic. For best performance, the storage, migration, and management networks should be split to avoid network saturation.
