import pulumi
from pulumi_azure_native import resources, containerservice

# Configurable variables
config = pulumi.Config()
resource_group_name = config.get('resourceGroupName') or 'llm-chat-rg'
location = config.get('location') or 'eastus'
cluster_name = config.get('clusterName') or 'llm-chat-aks'

# Resource group
resource_group = resources.ResourceGroup('resource-group',
    resource_group_name=resource_group_name,
    location=location)

# AKS cluster
aks_cluster = containerservice.ManagedCluster(
    'aks-cluster',
    resource_group_name=resource_group.name,
    location=resource_group.location,
    dns_prefix='llm-chat',
    agent_pool_profiles=[containerservice.ManagedClusterAgentPoolProfileArgs(
        name='agentpool',
        mode='System',
        count=3,
        vm_size='Standard_DS2_v2',
    )],
    identity=containerservice.ManagedClusterIdentityArgs(
        type='SystemAssigned'
    ),
)

pulumi.export('kubeconfig', containerservice.list_managed_cluster_user_credentials_output(
    resource_group_name=resource_group.name,
    resource_name=aks_cluster.name
).kubeconfigs[0].value.apply(lambda enc: enc.decode('utf-8')))
