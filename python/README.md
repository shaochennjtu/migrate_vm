# Migrate virtual machines from one host to another in the RHV environment.

Live migration
Live migration refers to the process of moving a virtual machine from one physical host to another while it is running. RHVM moves memory, storage, and network connectivity of the virtual machine from the original host machine to the destination. Live migration is useful to support maintenance tasks on hosts without disrupting your running virtual machines.

Live migration is transparent to the end-user. The virtual machine remains powered on, and user applications continue to run while the virtual machine is migrated to a new physical host runs. Clients communicating with the virtual machine should notice no more than a network pause of a few milliseconds as the transfer completes.

For live migration to work properly, the new host must have a CPU with the same architecture and features as the original host. Red Hat Virtualization helps you manage this by organizing hosts into clusters. A virtual machine may only migrate to hypervisor hosts that are members of its cluster. This helps you ensure that virtual machines do not migrate between machines that support a different set of processor features.
