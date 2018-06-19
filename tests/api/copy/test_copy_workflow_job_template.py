from fauxfactory import gen_boolean, gen_alpha, gen_choice
from towerkit.utils import poll_until
import pytest

from tests.api import Base_Api_Test
from tests.lib.helpers.copy_utils import check_fields


@pytest.mark.api
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_Copy_Workflow_Job_Template(Base_Api_Test):

    identical_fields = ['type', 'description', 'extra_vars', 'organization', 'survey_enabled', 'allow_simultaneous',
                        'ask_variables_on_launch']
    unequal_fields = ['id', 'created', 'modified']

    def check_node_fields(self, old_node, new_node, old_wfjt, new_wfjt):
        identical_fields = ['type', 'extra_data', 'job_type', 'job_tags', 'skip_tags', 'limit', 'diff_mode',
                            'verbosity']
        unequal_fields = ['id', 'created', 'modified']

        assert old_node.workflow_job_template == old_wfjt.id
        assert new_node.workflow_job_template == new_wfjt.id
        check_fields(old_node, new_node, identical_fields, unequal_fields)

    def add_child_node(self, endpoint, node):
        endpoint.connection.post(endpoint.endpoint, dict(id=node.id))

    def get_node_children(self, node, indexed_nodes):
        children = []
        children += [indexed_nodes[i] for i in node.success_nodes]
        children += [indexed_nodes[i] for i in node.failure_nodes]
        children += [indexed_nodes[i] for i in node.always_nodes]
        return children

    def get_root_nodes(self, indexed_nodes):
        roots = dict(indexed_nodes)
        for node in indexed_nodes.values():
            for child in self.get_node_children(node, indexed_nodes):
                for nid in roots:
                    if nid == child.id:
                        roots.pop(nid)
                        break

        return list(roots.values())

    def create_wfjt_with_nodes(self, v2, factories, num_nodes):
        post_options = v2.workflow_job_template_nodes.options().actions.POST
        job_types = dict(post_options.job_type.choices).keys()
        verbosities = dict(post_options.verbosity.choices).keys()
        wfjt = factories.v2_workflow_job_template()
        nodes = []
        for i in range(4):
            jt = factories.v2_job_template(ask_variables_on_launch=gen_boolean(), ask_job_type_on_launch=gen_boolean(),
                                           ask_tags_on_launch=gen_boolean(), ask_skip_tags_on_launch=gen_boolean(),
                                           ask_limit_on_launch=gen_boolean(), ask_verbosity_on_launch=gen_boolean(),
                                           ask_diff_mode_on_launch=gen_boolean())
            extra_data = '{"foo":"bar"}' if jt.ask_variables_on_launch else ''
            job_type = gen_choice(job_types) if jt.ask_job_type_on_launch else None
            job_tags = gen_alpha() if jt.ask_tags_on_launch else None
            skip_tags = gen_alpha() if jt.ask_skip_tags_on_launch else None
            limit = gen_alpha() if jt.ask_limit_on_launch else None
            verbosity = gen_choice(verbosities) if jt.ask_verbosity_on_launch else None
            diff_mode = gen_boolean() if jt.ask_diff_mode_on_launch else None
            nodes.append(factories.v2_workflow_job_template_node(workflow_job_template=wfjt, extra_data=extra_data,
                                                                 job_type=job_type, job_tags=job_tags,
                                                                 skip_tags=skip_tags, limit=limit, verbosity=verbosity,
                                                                 diff_mode=diff_mode, unified_job_template=jt))
        return wfjt

    def test_copy_normal(self, factories, copy_with_teardown):
        wfjt = factories.v2_workflow_job_template()
        new_wfjt = copy_with_teardown(wfjt)
        check_fields(wfjt, new_wfjt, self.identical_fields, self.unequal_fields)

    def test_copy_wfjt_with_non_default_values(self, factories, copy_with_teardown):
        wfjt = factories.v2_workflow_job_template(extra_vars='{"foo":"bar"}', survey_enabled=gen_boolean(),
                                                  allow_simultaneous=gen_boolean(),
                                                  ask_variables_on_launch=gen_boolean())
        new_wfjt = copy_with_teardown(wfjt)
        check_fields(wfjt, new_wfjt, self.identical_fields, self.unequal_fields)

    def test_copy_wfjt_labels(self, factories, copy_with_teardown):
        wfjt = factories.v2_workflow_job_template()
        label = factories.v2_label()
        wfjt.add_label(label)
        new_wfjt = copy_with_teardown(wfjt)

        old_labels = wfjt.related.labels.get()
        new_labels = new_wfjt.related.labels.get()

        check_fields(wfjt, new_wfjt, self.identical_fields, self.unequal_fields)
        assert old_labels.count == 1
        assert new_labels.count == old_labels.count
        assert new_labels.results[0].id == old_labels.results[0].id

    def test_copy_wfjt_survey_spec(self, factories, copy_with_teardown):
        wfjt = factories.v2_workflow_job_template()
        survey = [dict(required=False,
                       question_name='Test-1',
                       variable='var1',
                       type='password',
                       default='var1_default')]
        wfjt.add_survey(spec=survey)
        new_wfjt = copy_with_teardown(wfjt)

        old_survey = wfjt.related.survey_spec.get().json
        new_survey = new_wfjt.related.survey_spec.get().json

        check_fields(wfjt, new_wfjt, self.identical_fields, self.unequal_fields)
        assert new_survey == old_survey

    def test_copy_wfjt_nodes(self, v2, factories, copy_with_teardown):
        # Create a forest of wfjt nodes
        wfjt = self.create_wfjt_with_nodes(v2, factories, num_nodes=4)
        wfjt_nodes_pg = wfjt.related.workflow_nodes.get()
        assert wfjt_nodes_pg.count == 4

        nodes = wfjt_nodes_pg.results
        self.add_child_node(nodes[0].related.success_nodes, nodes[1])
        self.add_child_node(nodes[0].related.failure_nodes, nodes[2])
        self.add_child_node(nodes[1].related.always_nodes, nodes[3])

        # Make a copy
        old_wfjt = wfjt
        new_wfjt = copy_with_teardown(wfjt)
        check_fields(old_wfjt, new_wfjt, self.identical_fields, self.unequal_fields)
        poll_until(lambda: new_wfjt.related.workflow_nodes.get().count == wfjt_nodes_pg.count, timeout=30)

        # Traverse & compare the two graphs
        old_nodes = dict([(n.id, n) for n in wfjt_nodes_pg.get().results])
        new_nodes = dict([(n.id, n) for n in new_wfjt.related.workflow_nodes.get().results])
        assert len(old_nodes) == len(new_nodes)

        old_frontier = sorted(self.get_root_nodes(old_nodes), key=lambda n: n.unified_job_template)
        new_frontier = sorted(self.get_root_nodes(new_nodes), key=lambda n: n.unified_job_template)
        assert len(old_frontier) == len(new_frontier)
        while old_frontier:
            old_node = old_frontier.pop()
            new_node = new_frontier.pop()
            assert old_node.unified_job_template == new_node.unified_job_template
            self.check_node_fields(old_node, new_node, old_wfjt, new_wfjt)

            old_frontier.extend(sorted(self.get_node_children(old_node, old_nodes), key=lambda n: n.unified_job_template))
            new_frontier.extend(sorted(self.get_node_children(new_node, new_nodes), key=lambda n: n.unified_job_template))
        assert not new_frontier

    def test_copy_wfjt_node_references_with_permission(self, factories, copy_with_teardown):
        jt = factories.v2_job_template(ask_credential_on_launch=True, ask_inventory_on_launch=True)
        wfjt = factories.v2_workflow_job_template()
        wfjtn = factories.v2_workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt,
                                                        credential=jt.ds.credential, inventory=jt.ds.inventory)
        assert wfjtn.unified_job_template == jt.id
        assert wfjtn.inventory == jt.ds.inventory.id
        assert wfjtn.credential == jt.ds.credential.id

        new_wfjt = copy_with_teardown(wfjt)
        poll_until(lambda: new_wfjt.related.workflow_nodes.get().count == 1, timeout=30)
        check_fields(wfjt, new_wfjt, self.identical_fields, self.unequal_fields)

        new_wfjtn = new_wfjt.related.workflow_nodes.get().results[0]
        self.check_node_fields(wfjtn, new_wfjtn, wfjt, new_wfjt)
        assert wfjtn.unified_job_template == new_wfjtn.unified_job_template
        assert wfjtn.inventory == new_wfjtn.inventory
        assert wfjtn.credential == new_wfjtn.credential

    def test_copy_wfjt_node_references_without_permission(self, factories, copy_with_teardown, set_test_roles):
        orgA = factories.v2_organization()
        orgB = factories.v2_organization()
        cred = factories.v2_credential(kind='ssh', organization=orgA)
        inv = factories.v2_inventory(organization=orgA)
        jt = factories.v2_job_template(ask_credential_on_launch=True, ask_inventory_on_launch=True,
                                       credential=cred, inventory=inv)
        wfjt = factories.v2_workflow_job_template(organization=orgB)
        wfjtn = factories.v2_workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt,
                                                        credential=cred, inventory=inv)
        assert wfjtn.unified_job_template == jt.id
        assert wfjtn.inventory == inv.id
        assert wfjtn.credential == cred.id

        user = factories.user()
        set_test_roles(user, orgB, 'user', 'admin')

        with self.current_user(user):
            new_wfjt = copy_with_teardown(wfjt)
            poll_until(lambda: new_wfjt.related.workflow_nodes.get().count == 1, timeout=30)
            check_fields(wfjt, new_wfjt, self.identical_fields, self.unequal_fields)

            new_wfjtn = new_wfjt.related.workflow_nodes.get().results[0]
            self.check_node_fields(wfjtn, new_wfjtn, wfjt, new_wfjt)
            assert not new_wfjtn.unified_job_template
            assert not new_wfjtn.credential
            assert not new_wfjtn.inventory
