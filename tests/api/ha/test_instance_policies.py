import random

from towerkit import utils
from tests.lib.helpers import openshift_utils
import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.requires_ha
@pytest.mark.mp_group('TestInstancePolicies', 'serial')
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestInstancePolicies(Base_Api_Test):

    @pytest.fixture
    def tower_instance_hostnames(self, v2):
        return [instance.hostname for instance in v2.instances.get().results]

    @pytest.mark.parametrize('instance_percentage, expected_num_instances',
        [(0, 0), (20, 1), (50, 3), (79, 3), (100, 5)])
    def test_correct_instances_with_new_ig_with_policy_instance_percentage(self, factories, tower_instance_hostnames,
                                                                           instance_percentage, expected_num_instances):
        ig = factories.instance_group(policy_instance_percentage=instance_percentage)
        assert ig.instances == expected_num_instances

        ig_instances = ig.related.instances.get()
        ig_instance_hostnames = [instance.hostname for instance in ig_instances.results]
        assert ig_instances.count == expected_num_instances
        assert len(ig_instance_hostnames) == expected_num_instances
        assert set(ig_instance_hostnames) < set(tower_instance_hostnames)

    @pytest.mark.parametrize('instance_minimum, expected_num_instances',
        [(0, 0), (3, 3), (5, 5), (777, 5)])
    def test_correct_instances_with_new_ig_with_policy_instance_minimum(self, factories, tower_instance_hostnames,
                                                                        instance_minimum, expected_num_instances):
        ig = factories.instance_group(policy_instance_minimum=instance_minimum)
        assert ig.instances == expected_num_instances

        ig_instances = ig.related.instance.get()
        ig_instance_hostnames = [instance.hostname for instance in ig_instances.results]
        assert ig_instances.count == expected_num_instances
        assert len(ig_instance_hostnames) == expected_num_instances
        assert set(ig_instance_hostnames) < set(tower_instance_hostnames)

    def test_correct_instances_with_new_ig_with_policy_instance_list(self, factories, tower_instance_hostnames):
        instances = random.sample(tower_instance_hostnames, 3)
        ig = factories.v2_instance_group(policy_instance_list=instances)
        assert ig.instances == len(instances)
        assert set(ig.policy_instance_list) == set(instances)

        ig_instances = ig.related.instance.get()
        ig_instance_hostnames = [instance.hostname for instance in ig_instances.results]
        assert ig_instances.count == len(instances)
        assert len(ig_instance_hostnames) == len(instances)
        assert set(ig_instance_hostnames) < set(tower_instance_hostnames)

    def test_correct_instances_with_existing_ig_with_updated_policy_instance_percentage(self, factories,
                                                                                        tower_instance_hostnames):
        ig = factories.instance_group(policy_instance_percentage=0)
        assert ig.instances == 0

        ig.policy_instance_percentage = 100

        ig_instances = ig.related.instance.get()
        ig_instance_hostnames = [instance.hostname for instance in ig_instances]
        assert ig_instances.count == 5
        assert set(ig_instance_hostnames) == set(tower_instance_hostnames)

    def test_correct_instances_with_existing_ig_with_updated_policy_instance_minimum(self, factories,
                                                                                     tower_instance_hostnames):
        ig = factories.instance_group(policy_instance_minimum=0)
        assert ig.instances == 0

        ig.policy_instance_minimum = 5

        ig_instances = ig.related.instances.get()
        ig_instance_hostnames = [instance.hostname for instance in ig_instances]
        assert ig_instances.count == 5
        assert set(ig_instance_hostnames) == set(tower_instance_hostnames)

    def test_correct_instances_with_existing_ig_with_updated_policity_instance_list(self, factories,
                                                                                    tower_instance_hostnames):
        ig = factories.instance_group()
        assert ig.instances == 0

        ig.policy_instance_list = tower_instance_hostnames

        ig_instances = ig.related.instances.get()
        ig_instance_hostnames = [instance.hostname for instance in ig_instances]
        assert ig_instances.count == 5
        assert set(ig_instance_hostnames) == set(tower_instance_hostnames)

    def test_manual_instance_association_updates_instance_group_attributes(self, factories, v2):
        ig = factories.instance_group()
        instance = v2.instances.get().results.pop()
        assert ig.instances == 0

        ig.add_instance(instance)
        assert ig.get().instances == 1
        assert len(ig.policy_instance_list) == 1
        assert ig.policy_instance_list.pop() == instance.hostname

        ig_instances = ig.related.instances.get()
        assert ig_instances.count == 1
        assert len(ig_instances.results) == 1
        assert ig_instances.results.pop().hostname == instance.hostname

    def test_manual_instance_disassociation_updates_instance_group_attributes(self, factories, v2):
        ig = factories.instance_group(policy_instance_percentage=100)
        instance = v2.instances.get().results.pop()
        assert ig.instances == 5

        ig.remove_instance(instance)
        assert ig.get().instances == 4

        ig_instances = ig.related.instances.get()
        ig_instance_hostnames = [i.hostname for i in ig_instances.results]
        assert ig_instances.count == 4
        assert len(ig_instances.results) == 4
        assert instance.hostname not in ig_instance_hostnames

    def test_manual_association_removes_instance_from_consideration_from_other_igs(self, factories, v2):
        pct_ig = factories.instance_group(policy_instance_percentage=100)
        min_ig = factories.instance_group(policy_instance_minimum=5)
        mixed_policy_ig = factories.instance_group(policy_instance_percentage=100,
                                                   policy_instance_minimum=5)

        for ig in (pct_ig, min_ig, mixed_policy_ig):
            assert ig.get().instances == 5

        ig = factories.instance_group()
        instance = v2.instances.get().results.pop()
        ig.add_instance(instance)

        for ig in (pct_ig, min_ig, mixed_policy_ig):
            assert ig.get().instances == 4
            assert instance.hostname not in [i.hostname for i in ig.results]

    def test_manual_disassociation_instroduces_instance_to_consideration_from_other_igs(self, factories, v2):
        ig = factories.instance_group()
        instance = v2.instances.get().results.pop()
        ig.add_instance(instance)

        pct_ig = factories.instance_group(policy_instance_percentage=100)
        min_ig = factories.instance_group(policy_instance_minimum=5)
        mixed_policy_ig = factories.instance_group(policy_instance_percentage=100,
                                                   policy_instance_minimum=5)

        for ig in (pct_ig, min_ig, mixed_policy_ig):
            assert ig.get().instances == 4
            assert instance.hostname not in [i.hostname for i in ig.results]

        ig.remove_instance(instance)

        for ig in (pct_ig, min_ig, mixed_policy_ig):
            assert ig.get().instances == 5
            assert instance.hostname in [i.hostname for i in ig.results]

    @pytest.mark.requires_openshift_ha
    def test_instance_groups_update_for_newly_spawned_instance(self, factories, v2):
        assert v2.instances.get().count == 5

        pct_ig = factories.instance_group(policy_instance_percentage=100)
        min_ig = factories.instance_group(policy_instance_minimum=5)
        mixed_policy_ig = factories.instance_group(policy_instance_percentage=100,
                                                   policy_instance_minimum=5)

        assert pct_ig.instances == 5
        assert min_ig.instances == 5
        assert mixed_policy_ig.instances == 5

        openshift_utils.scale_dc(dc='tower', replicas=6)

        utils.poll_until(lambda: pct_ig.get().instances == 6, interval=1, timeout=60)
        utils.poll_until(lambda: min_ig.get().instances == 6, interval=1, timeout=60)
        utils.poll_until(lambda: mixed_policy_ig.get().instances == 6, interval=1, timeout=60)

    @pytest.mark.requires_openshift_ha
    def test_instance_groups_update_for_newly_removed_instance(self, factories, v2):
        assert v2.instances.get().count == 6

        pct_ig = factories.instance_group(policy_instance_percentage=100)
        min_ig = factories.instance_group(policy_instance_minimum=5)
        mixed_policy_ig = factories.instance_group(policy_instance_percentage=100,
                                                   policy_instance_minimum=5)

        assert pct_ig.instances == 6
        assert min_ig.instances == 6
        assert mixed_policy_ig.instances == 6

        openshift_utils.scale_dc(dc='tower', replicas=5)

        utils.poll_until(lambda: pct_ig.get().instances == 5, interval=1, timeout=60)
        utils.poll_until(lambda: min_ig.get().instances == 5, interval=1, timeout=60)
        utils.poll_until(lambda: mixed_policy_ig.get().instances == 5, interval=1, timeout=60)
