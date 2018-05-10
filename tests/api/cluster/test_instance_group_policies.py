from collections import Counter
import random

from towerkit import utils
import pytest

from tests.lib.helpers import openshift_utils
from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.requires_cluster
@pytest.mark.mp_group('InstanceGroupPolicies', 'serial')
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestInstanceGroupPolicies(Base_Api_Test):

    def get_ig_instances(self, ig):
        return [instance.hostname for instance in ig.related.instances.get().results]

    @pytest.fixture(autouse=True, scope='class')
    def preflight_check(self, authtoken, v2_class):
        tower_ig = v2_class.instance_groups.get(name='tower').results.pop()
        if tower_ig.related.instances.get().count != 5:
            pytest.skip('Tests require five non-isolated instances.')

    @pytest.fixture
    def tower_instance_hostnames(self, tower_instance_group):
        return [instance.hostname for instance in tower_instance_group.related.instances.get().results]

    @pytest.mark.github('https://github.com/ansible/tower/issues/881')
    @pytest.mark.parametrize('instance_percentage, expected_num_instances',
        [(0, 0), (20, 1), (41, 2), (79, 3), (100, 5)])
    def test_correct_instances_with_new_ig_with_policy_instance_percentage(self, factories, tower_instance_hostnames,
                                                                           instance_percentage, expected_num_instances):
        ig = factories.instance_group(policy_instance_percentage=instance_percentage)
        utils.poll_until(lambda: ig.get().instances == expected_num_instances, interval=1, timeout=30)

        ig_instances = ig.related.instances.get()
        ig_instance_hostnames = self.get_ig_instances(ig)
        assert ig_instances.count == expected_num_instances
        assert len(ig_instance_hostnames) == expected_num_instances
        if instance_percentage != 100:
            assert set(ig_instance_hostnames) < set(tower_instance_hostnames)
        else:
            assert set(ig_instance_hostnames) == set(tower_instance_hostnames)

    @pytest.mark.parametrize('instance_minimum, expected_num_instances',
        [(0, 0), (3, 3), (5, 5), (777, 5)])
    def test_correct_instances_with_new_ig_with_policy_instance_minimum(self, factories, tower_instance_hostnames,
                                                                        instance_minimum, expected_num_instances):
        ig = factories.instance_group(policy_instance_minimum=instance_minimum)
        utils.poll_until(lambda: ig.get().instances == expected_num_instances, interval=1, timeout=30)

        ig_instances = ig.related.instances.get()
        ig_instance_hostnames = self.get_ig_instances(ig)
        assert ig_instances.count == expected_num_instances
        assert len(ig_instance_hostnames) == expected_num_instances
        if instance_minimum not in (5, 777):
            assert set(ig_instance_hostnames) < set(tower_instance_hostnames)
        else:
            assert set(ig_instance_hostnames) == set(tower_instance_hostnames)

    @pytest.mark.parametrize('tower_instances', [0, 1, 2, 3])
    def test_correct_instances_with_new_ig_with_policy_instance_list(self, factories, tower_instance_hostnames,
                                                                     tower_instances):
        instances = random.sample(tower_instance_hostnames, tower_instances)
        ig = factories.instance_group(policy_instance_list=instances)
        utils.poll_until(lambda: ig.get().instances == len(instances), interval=1, timeout=30)
        assert set(ig.policy_instance_list) == set(instances)

        ig_instances = ig.related.instances.get()
        ig_instance_hostnames = self.get_ig_instances(ig)
        assert ig_instances.count == len(instances)
        assert len(ig_instance_hostnames) == len(instances)
        assert set(ig_instance_hostnames) < set(tower_instance_hostnames)

    def test_correct_instances_with_new_ig_with_multiple_rules(self, factories, v2, tower_instance_hostnames):
        ig = factories.instance_group(policy_instance_percentage=20, policy_instance_minimum=3,
                                      policy_instance_list=tower_instance_hostnames)
        utils.poll_until(lambda: ig.get().instances == 5, interval=1, timeout=30)
        assert set(ig.policy_instance_list) == set(tower_instance_hostnames)

        ig_instances = ig.related.instances.get()
        ig_instance_hostnames = self.get_ig_instances(ig)
        assert ig_instances.count == 5
        assert len(ig_instance_hostnames) == 5
        assert set(ig_instance_hostnames) == set(tower_instance_hostnames)

        # verify instance disassociation
        instances = v2.instances.get().results
        for instance in instances:
            ig.remove_instance(instance)
        utils.poll_until(lambda: ig.get().instances == 0, interval=1, timeout=30)
        assert ig_instances.get().count == 0
        assert ig.policy_instance_list == []

    @pytest.mark.github('https://github.com/ansible/tower/issues/873')
    def test_correct_instances_with_existing_ig_with_updated_policy_instance_percentage(self, factories,
                                                                                        tower_instance_hostnames):
        ig = factories.instance_group(policy_instance_percentage=0)
        assert ig.instances == 0

        ig.policy_instance_percentage = 100
        utils.poll_until(lambda: ig.get().instances == 5, interval=1, timeout=30)

        ig_instances = ig.related.instances.get()
        ig_instance_hostnames = self.get_ig_instances(ig)
        assert ig_instances.count == 5
        assert set(ig_instance_hostnames) == set(tower_instance_hostnames)

    @pytest.mark.github('https://github.com/ansible/tower/issues/873')
    def test_correct_instances_with_existing_ig_with_updated_policy_instance_minimum(self, factories,
                                                                                     tower_instance_hostnames):
        ig = factories.instance_group(policy_instance_minimum=0)
        assert ig.instances == 0

        ig.policy_instance_minimum = 5
        utils.poll_until(lambda: ig.get().instances == 5, interval=1, timeout=30)

        ig_instances = ig.related.instances.get()
        ig_instance_hostnames = self.get_ig_instances(ig)
        assert ig_instances.count == 5
        assert set(ig_instance_hostnames) == set(tower_instance_hostnames)

    @pytest.mark.github('https://github.com/ansible/tower/issues/873')
    def test_correct_instances_with_existing_ig_with_updated_policy_instance_list(self, factories, tower_instance_hostnames):
        ig = factories.instance_group()
        assert ig.instances == 0

        ig.policy_instance_list = tower_instance_hostnames
        utils.poll_until(lambda: ig.get().instances == 5, interval=1, timeout=30)

        ig_instances = ig.related.instances.get()
        ig_instance_hostnames = self.get_ig_instances(ig)
        assert ig_instances.count == 5
        assert set(ig_instance_hostnames) == set(tower_instance_hostnames)

    def test_single_instances_are_distributed_evenly_with_igs_with_policy_instance_percentage(self, factories,
                                                                                              tower_instance_hostnames):
        igs = []
        for _ in range(5):
            ig = factories.instance_group(policy_instance_percentage=20)
            utils.poll_until(lambda: ig.get().instances == 1, interval=1, timeout=30)
            igs.append(ig)

        sourced_instances = []
        for ig in igs:
            sourced_instances += self.get_ig_instances(ig)
        assert set(sourced_instances) == set(tower_instance_hostnames)

    def test_single_instances_are_distributed_evenly_with_igs_with_policy_instance_minimum(self, factories,
                                                                                           tower_instance_hostnames):
        igs = []
        for _ in range(5):
            ig = factories.instance_group(policy_instance_minimum=1)
            utils.poll_until(lambda: ig.get().instances == 1, interval=1, timeout=30)
            igs.append(ig)

        sourced_instances = []
        for ig in igs:
            sourced_instances += self.get_ig_instances(ig)
        assert set(sourced_instances) == set(tower_instance_hostnames)

    def test_single_instances_are_distributed_evenly_with_igs_with_different_rules(self, factories,
                                                                                   tower_instance_hostnames):
        ig1, ig2 = [factories.instance_group(policy_instance_minimum=1) for _ in range(2)]
        ig3, ig4 = [factories.instance_group(policy_instance_percentage=20) for _ in range(2)]
        ig5 = factories.instance_group(policy_instance_minimum=1, policy_instance_percentage=20)

        for ig in (ig1, ig2, ig3, ig4, ig5):
            utils.poll_until(lambda: ig.get().instances == 1, interval=1, timeout=30)

        sourced_instances = []
        for ig in (ig1, ig2, ig3, ig4, ig5):
            sourced_instances += self.get_ig_instances(ig)
        assert set(sourced_instances) == set(tower_instance_hostnames)

    def test_multiple_instances_are_distributed_evenly_with_igs_with_policy_instance_percentage(self, factories,
                                                                                                tower_instance_hostnames):
        igs = []
        for _ in range(5):
            ig = factories.instance_group(policy_instance_percentage=60)
            utils.poll_until(lambda: ig.get().instances == 3, interval=1, timeout=30)
            igs.append(ig)

            ig_hostnames = self.get_ig_instances(ig)
            assert len(set(ig_hostnames)) == 3
            assert set(ig_hostnames) < set(tower_instance_hostnames)

        sourced_instances = []
        for ig in igs:
            sourced_instances += self.get_ig_instances(ig)

        counter = Counter(sourced_instances)
        for hostname in counter:
            assert counter[hostname] == 3

    def test_multiple_instances_are_distributed_evenly_with_igs_with_policy_instance_minimum(self, factories,
                                                                                             tower_instance_hostnames):
        igs = []
        for _ in range(5):
            ig = factories.instance_group(policy_instance_minimum=3)
            utils.poll_until(lambda: ig.get().instances == 3, interval=1, timeout=30)
            igs.append(ig)

            ig_hostnames = self.get_ig_instances(ig)
            assert len(set(ig_hostnames)) == 3
            assert set(ig_hostnames) < set(tower_instance_hostnames)

        sourced_instances = []
        for ig in igs:
            sourced_instances += self.get_ig_instances(ig)

        counter = Counter(sourced_instances)
        for hostname in counter:
            assert counter[hostname] == 3

    def test_multiple_instances_are_distributed_evenly_with_igs_with_different_rules(self, factories,
                                                                                     tower_instance_hostnames):
        pct_ig = factories.instance_group(policy_instance_percentage=100)
        min_ig = factories.instance_group(policy_instance_minimum=5)
        mixed_policy_ig = factories.instance_group(policy_instance_percentage=100,
                                                   policy_instance_minimum=3)

        for igroup in (pct_ig, min_ig, mixed_policy_ig):
            utils.poll_until(lambda: igroup.get().instances == 5, interval=1, timeout=30)

        for igroup in (pct_ig, min_ig, mixed_policy_ig):
            ig_instances = self.get_ig_instances(igroup)
            assert set(ig_instances) == set(tower_instance_hostnames)

    def test_manual_instance_association_updates_instance_group_attributes(self, factories, v2):
        instance = v2.instances.get().results.pop()
        ig = factories.instance_group()
        assert ig.instances == 0

        ig.add_instance(instance)
        assert ig.get().instances == 1
        assert ig.policy_instance_list == [instance.hostname]

        ig_instances = ig.related.instances.get()
        assert ig_instances.count == 1
        assert len(ig_instances.results) == 1
        assert ig_instances.results.pop().hostname == instance.hostname

    def test_manual_instance_disassociation_updates_instance_group_attributes(self, factories, v2):
        ig = factories.instance_group(policy_instance_percentage=100)
        utils.poll_until(lambda: ig.get().instances == 5, interval=1, timeout=30)

        instance = v2.instances.get().results.pop()
        ig.remove_instance(instance)
        assert ig.get().instances == 4

        ig_instances = ig.related.instances.get()
        ig_instance_hostnames = self.get_ig_instances(ig)
        assert ig_instances.count == 4
        assert len(ig_instances.results) == 4
        assert instance.hostname not in ig_instance_hostnames

    def test_manual_instance_association_removes_instance_from_consideration_from_other_igs(self, factories, v2):
        pct_ig = factories.instance_group(policy_instance_percentage=100)
        min_ig = factories.instance_group(policy_instance_minimum=5)
        mixed_policy_ig = factories.instance_group(policy_instance_percentage=100,
                                                   policy_instance_minimum=5)

        for igroup in (pct_ig, min_ig, mixed_policy_ig):
            utils.poll_until(lambda: igroup.get().instances == 5, interval=1, timeout=30)

        ig = factories.instance_group()
        instance = v2.instances.get().results.pop()
        ig.add_instance(instance)

        for igroup in (pct_ig, min_ig, mixed_policy_ig):
            utils.poll_until(lambda: igroup.get().instances == 4, interval=1, timeout=30)
            assert instance.hostname not in self.get_ig_instances(igroup)

    def test_manual_instance_disassociation_introduces_instance_for_consideration_to_other_igs(self, factories, v2):
        ig = factories.instance_group()
        instance = v2.instances.get().results.pop()
        ig.add_instance(instance)

        pct_ig = factories.instance_group(policy_instance_percentage=100)
        min_ig = factories.instance_group(policy_instance_minimum=5)
        mixed_policy_ig = factories.instance_group(policy_instance_percentage=100,
                                                   policy_instance_minimum=5)

        for igroup in (pct_ig, min_ig, mixed_policy_ig):
            utils.poll_until(lambda: igroup.get().instances == 4, interval=1, timeout=30)
            assert instance.hostname not in self.get_ig_instances(igroup)

        ig.remove_instance(instance)

        for igroup in (pct_ig, min_ig, mixed_policy_ig):
            utils.poll_until(lambda: igroup.get().instances == 5, interval=1, timeout=30)
            assert instance.hostname in self.get_ig_instances(igroup)

    def test_tower_ig_unaffected_by_manual_instance_association_and_disassociation_in_other_igs(self, factories, v2,
                                                                                                tower_instance_group):
        tower_ig_instances = tower_instance_group.related.instances.get()
        assert tower_instance_group.instances == 5
        assert tower_ig_instances.count == 5

        ig = factories.instance_group()
        instance = v2.instances.get().results.pop()
        ig.add_instance(instance)
        utils.poll_until(lambda: ig.get().instances == 1, interval=1, timeout=30)

        assert tower_instance_group.get().instances == 5
        assert tower_ig_instances.get().count == 5

        ig.remove_instance(instance)
        utils.poll_until(lambda: ig.get().instances == 0, interval=1, timeout=30)

        assert tower_instance_group.get().instances == 5
        assert tower_ig_instances.get().count == 5

    @pytest.mark.requires_openshift_cluster
    def test_instance_groups_update_for_newly_spawned_instance(self, factories, v2, tower_instance_hostnames):
        num_instances = len(tower_instance_hostnames)

        pct_ig = factories.instance_group(policy_instance_percentage=100)
        min_ig = factories.instance_group(policy_instance_minimum=777)
        mixed_policy_ig = factories.instance_group(policy_instance_percentage=100,
                                                   policy_instance_minimum=777)

        for igroup in (pct_ig, min_ig, mixed_policy_ig):
            utils.poll_until(lambda: igroup.get().instances == num_instances, interval=1, timeout=30)

        openshift_utils.prep_environment()
        openshift_utils.scale_dc(dc='tower', replicas=num_instances + 1)
        utils.poll_until(lambda: v2.instances.get(cpu__gt=0).count == num_instances + 1, interval=5, timeout=600)

        for igroup in (pct_ig, min_ig, mixed_policy_ig):
            utils.poll_until(lambda: igroup.get().instances == num_instances + 1, interval=1, timeout=30)

    @pytest.mark.requires_openshift_cluster
    def test_instance_groups_update_for_newly_removed_instance(self, factories, v2, tower_instance_hostnames):
        num_instances = len(tower_instance_hostnames)

        pct_ig = factories.instance_group(policy_instance_percentage=100)
        min_ig = factories.instance_group(policy_instance_minimum=777)
        mixed_policy_ig = factories.instance_group(policy_instance_percentage=100,
                                                   policy_instance_minimum=777)

        for igroup in (pct_ig, min_ig, mixed_policy_ig):
            utils.poll_until(lambda: igroup.get().instances == num_instances, interval=1, timeout=30)

        openshift_utils.prep_environment()
        openshift_utils.scale_dc(dc='tower', replicas=num_instances - 1)
        utils.poll_until(lambda: v2.instances.get(cpu__gt=0).count == num_instances - 1, interval=5, timeout=600)

        for igroup in (pct_ig, min_ig, mixed_policy_ig):
            utils.poll_until(lambda: igroup.get().instances == num_instances - 1, interval=1, timeout=30)
