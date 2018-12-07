# Shared functions for workflow tests that run jobs


def get_job_node(wfj, wfj_node_id, mapping):
    """Given a WFJ, the WFJ node id, and the proper mapping object, return the node.

    Example:
        host = factories.v2_host()
        wfjt = factories.workflow_job_template()
        jt_failure = factories.job_template(inventory=host.ds.inventory, allow_simultaneous=True, playbook='fail_unless.yml')

        # create first node that will fail
        n1 = factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt_failure)
        # add "success node" that will then not run
        n2 = l1n1.related.success_nodes.post(dict(unified_job_template=jt.id))

        wfj = wfjt.launch().wait_until_completed()
        tree = WorkflowTree(wfjt)
        job_tree = WorkflowTree(wfj)
        mapping = WorkflowTreeMapper(tree, job_tree).map()
        job_tree = WorkflowTree(wfj)
        mapping = WorkflowTreeMapper(tree, job_tree).map()


        # Assert correct nodes get marked do_not_run
        assert get_job_node(wfj, n2.id, mapping).do_not_run is True
    """
    return wfj.related.workflow_nodes.get(
        id=mapping[wfj_node_id]).results.pop()


def get_job_status(wfj, wfj_node_id, mapping):
    """Given the WFJ, WFJ node id, and proper mapping object, return the job's current status if it exists.

    Example:
        host = factories.v2_host()
        wfjt = factories.workflow_job_template()
        jt_failure = factories.job_template(inventory=host.ds.inventory, allow_simultaneous=True, playbook='fail_unless.yml')

        # create node that will fail
        n1 = factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt_failure)

        wfj = wfjt.launch().wait_until_completed()
        tree = WorkflowTree(wfjt)
        job_tree = WorkflowTree(wfj)
        mapping = WorkflowTreeMapper(tree, job_tree).map()
        job_tree = WorkflowTree(wfj)
        mapping = WorkflowTreeMapper(tree, job_tree).map()


        # Assert correct nodes get marked do_not_run
        assert 'failed'  is get_job_status(wfj, n1.id, mapping)
    """
    return get_job_node(wfj, wfj_node_id, mapping)['summary_fields']['job']['status']
