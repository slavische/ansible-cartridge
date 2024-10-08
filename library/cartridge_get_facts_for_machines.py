from ansible.module_utils.helpers import Helpers as helpers

argument_spec = {
    'module_hostvars': {'required': True, 'type': 'dict'},
    'cluster_disabled_instances': {'required': True, 'type': 'list'},
    'play_hosts': {'required': True, 'type': 'list'},
}


def get_machine_id(instance_vars, instance_name):
    if 'ansible_host' not in instance_vars:
        raise Exception('Instance %s has not "ansible_host" option!' % instance_name)

    machine_id = '%s:%s' % (
        instance_vars['ansible_host'],
        instance_vars.get('ansible_port', 22)
    )

    return machine_id


def get_facts_for_machines(params):
    module_hostvars = params['module_hostvars']
    cluster_disabled_instances = params['cluster_disabled_instances']
    play_hosts = params['play_hosts']

    single_instances_for_each_machine = {}
    single_instances_for_each_machine_with_disabled = {}
    instances_by_machines = {}
    instances_from_same_machine = {}

    for instance_name in sorted(play_hosts):
        instance_vars = module_hostvars[instance_name]
        machine_id = get_machine_id(instance_vars, instance_name)

        # Calculate play hosts for each machine
        instances_by_machines[machine_id] = instances_by_machines.get(machine_id, [])
        instances_by_machines[machine_id].append(instance_name)

        # Copy link to machine list
        instances_from_same_machine[instance_name] = instances_by_machines[machine_id]

        # Calculate single enabled instance for each machine
        if all([
            helpers.is_enabled(instance_vars),
            instance_name not in cluster_disabled_instances,
            machine_id not in single_instances_for_each_machine,
        ]):
            single_instances_for_each_machine[machine_id] = instance_name
        # Calculate single not expelled instance for each machine
        elif all([
            not helpers.is_expelled(instance_vars),
            machine_id not in single_instances_for_each_machine_with_disabled,
        ]):
            single_instances_for_each_machine_with_disabled[machine_id] = instance_name

    # If there is no enabled instance, then check for the presence of a disabled (not expelled) one
    for machine_id, instance_name in single_instances_for_each_machine_with_disabled.items():
        if machine_id not in single_instances_for_each_machine:
            single_instances_for_each_machine[machine_id] = instance_name

    return helpers.ModuleRes(
        changed=False,
        single_instances_for_each_machine=list(single_instances_for_each_machine.values()),
        instances_from_same_machine=instances_from_same_machine,
    )


if __name__ == '__main__':
    helpers.execute_module(argument_spec, get_facts_for_machines)
