#!/usr/bin/env bats

source ../../lib/common

# function retrieve_awx_setup_path_based_on_version_and_scenario
#
@test "retrieve_boolean_value[yes]" {
    run retrieve_boolean_value yes
    echo "Status: ${status} | Ouput: ${output}"
    [[ "$status" -eq 0 ]]
    [[ "$output" = "true" ]]
}

@test "retrieve_boolean_value[no]" {
    run retrieve_boolean_value no
    echo "Status: ${status} | Ouput: ${output}"
    [[ "$status" -eq 0 ]]
    [[ "$output" = "false" ]]
}

@test "retrieve_boolean_value[other]" {
    run retrieve_boolean_value other
    echo "Status: ${status} | Ouput: ${output}"
    [[ "$status" -eq 1 ]]
    [[ "$output" =~ .*"cannot be casted".* ]]
}

# function generate_instance_name_prefix
#
@test "generate_instance_name_prefix[staging-repo]" {
    run generate_instance_name_prefix \
        instance-name-prefix platform\
        devel devel
    echo "Status: ${status} | Ouput: ${output}"
    [[ "$status" -eq 0 ]]
    [[ "$output" = "instance-name-prefix-ansible-devel-platform" ]]
}


# function setup_env_based_on_deployment_scenario
#
@test "setup_env_based_on_deployment_scenario[standalone]" {
    setup_env_based_on_deployment_scenario standalone
    echo "PLAYBOOK: ${PLAYBOOK} | INVENTORY: ${INVENTORY} | IMAGE_VARS: ${IMAGE_VARS}"
    [[ "$PLAYBOOK" = "playbooks/deploy-tower.yml" ]]
    [[ "$INVENTORY" = "playbooks/inventory.log" ]]
    [[ "$IMAGE_VARS" = "playbooks/images-ec2.yml" ]]
}

@test "setup_env_based_on_deployment_scenario[cluster]" {
    setup_env_based_on_deployment_scenario cluster
    echo "PLAYBOOK: ${PLAYBOOK} | INVENTORY: ${INVENTORY} | IMAGE_VARS: ${IMAGE_VARS}"
    [[ "$PLAYBOOK" = "playbooks/deploy-tower-cluster.yml" ]]
    [[ "$INVENTORY" = "playbooks/inventory.cluster" ]]
    [[ "$IMAGE_VARS" = "playbooks/images-isolated-groups.yml" ]]
}

@test "setup_env_based_on_deployment_scenario[nonexistent]" {
    run setup_env_based_on_deployment_scenario nonexistent
    echo "Status: ${status} | Ouput: ${output}"
    [[ "$status" -eq 1 ]]
    [[ "$output" =~ .*"is not a supported scenario".* ]]
}


# function retrieve_aw_repo_url_based_on_version
#
# NOTE(spredzy): Maybe mock the curl call so this doesn't
#                require internet connection to work.
@test "retrieve_aw_repo_url_based_on_version[3.3.3]" {
    run retrieve_aw_repo_url_based_on_version 3.3.3
    echo "Status: ${status} | Ouput: ${output}"
    [[ "$status" -eq 0 ]]
    [[ "$output" = "https://releases.ansible.com/ansible-tower" ]]
}

@test "retrieve_aw_repo_url_based_on_version[devel]" {
    run retrieve_aw_repo_url_based_on_version devel
    echo "Status: ${status} | Ouput: ${output}"
    [[ "$status" -eq 0 ]]
    [[ "$output" = "http://nightlies.testing.ansible.com/ansible-tower_nightlies_m8u16fz56qr6q7/devel" ]]
}

@test "retrieve_aw_repo_url_based_on_version[doesnotexist]" {
    run retrieve_aw_repo_url_based_on_version doesnotexist
    echo "Status: ${status} | Ouput: ${output}"
    [[ "$status" -eq 1 ]]
    [[ "$output" =~ .*"cannot be found".* ]]
}

# function retrieve_awx_setup_path_based_on_version_and_scenario
#
@test "retrieve_awx_setup_path_based_on_version_and_scenario[3.2.8:standalone]" {
    run retrieve_awx_setup_path_based_on_version_and_scenario \
        3.2.8 standalone https://releases.ansible.com/ansible-tower
    echo "Status: ${status} | Ouput: ${output}"
    [[ "$status" -eq 0 ]]
    [[ "$output" = "/setup/ansible-tower-setup-3.2.8.tar.gz" ]]
}

@test "retrieve_awx_setup_path_based_on_version_and_scenario[3.3.2:standalone]" {
    run retrieve_awx_setup_path_based_on_version_and_scenario \
        3.3.2 standalone https://releases.ansible.com/ansible-tower
    echo "Status: ${status} | Ouput: ${output}"
    [[ "$status" -eq 0 ]]
    [[ "$output" = "/setup/ansible-tower-setup-3.3.2-1.tar.gz" ]]
}

@test "retrieve_awx_setup_path_based_on_version_and_scenario[devel:standalone]" {
    run retrieve_awx_setup_path_based_on_version_and_scenario \
        devel standalone http://nightlies.testing.ansible.com/ansible-tower_nightlies_m8u16fz56qr6q7/devel
    echo "Status: ${status} | Ouput: ${output}"
    [[ "$status" -eq 0 ]]
    [[ "$output" = "/setup/ansible-tower-setup-latest.tar.gz" ]]
}

@test "retrieve_awx_setup_path_based_on_version_and_scenario[3.2.8:standalone-bundle]" {
    run retrieve_awx_setup_path_based_on_version_and_scenario \
        3.2.8 standalone-bundle https://releases.ansible.com/ansible-tower yes
    echo "Status: ${status} | Ouput: ${output}"
    [[ "$status" -eq 0 ]]
    [[ "$output" = "/setup-bundle/ansible-tower-setup-bundle-3.2.8-1.el7.tar.gz" ]]
}

@test "retrieve_awx_setup_path_based_on_version_and_scenario[3.3.2:standalone-bundle]" {
    run retrieve_awx_setup_path_based_on_version_and_scenario \
        3.3.2 standalone-bundle https://releases.ansible.com/ansible-tower yes
    echo "Status: ${status} | Ouput: ${output}"
    [[ "$status" -eq 0 ]]
    [[ "$output" = "/setup-bundle/ansible-tower-setup-bundle-3.3.2-1.el7.tar.gz" ]]
}

@test "retrieve_awx_setup_path_based_on_version_and_scenario[devel:standalone-bundle]" {
    run retrieve_awx_setup_path_based_on_version_and_scenario \
        devel standalone-bundle http://nightlies.testing.ansible.com/ansible-tower_nightlies_m8u16fz56qr6q7/devel yes
    echo "Status: ${status} | Ouput: ${output}"
    [[ "$status" -eq 0 ]]
    [[ "$output" = "/setup-bundle/ansible-tower-setup-bundle-latest.el7.tar.gz" ]]
}

@test "is_tower_cluster[true]" {
    local inventory="$(mktemp)"
    echo "[cluster_installer]" > "${inventory}"
    run is_tower_cluster "${inventory}"
    [ "${status}" -eq 0 ]
}

@test "is_tower_cluster[false]" {
    local inventory="$(mktemp)"
    echo "not_cluster" > "${inventory}"
    run is_tower_cluster "${inventory}"
    [ "${status}" -eq 1 ]
}
