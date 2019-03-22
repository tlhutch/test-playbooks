pipeline {

    agent { label 'jenkins-jnlp-agent' }

    parameters {
        choice(
            name: 'PRODUCT',
            description: 'Product to deploy',
            choices: ['awx', 'tower']
        )
        choice(
            name: 'SCENARIO',
            description: 'Deployment scenario for Tower',
            choices: ['standalone', 'cluster']
        )
        string(
            name: 'TOWER_FORK',
            description: 'Fork of tower to deploy',
            defaultValue: 'ansible'
        )
        string(
            name: 'TOWER_BRANCH',
            description: 'Branch to use for Tower',
            defaultValue: 'devel'
        )
        string(
            name: 'TOWER_PACKAGING_FORK',
            description: 'Fork of tower-packaging to deploy',
            defaultValue: 'ansible'
        )
        string(
            name: 'TOWER_PACKAGING_BRANCH',
            description: 'Branch to use for tower-packaging',
            defaultValue: 'devel'
        )
        string(
            name: 'TOWER_QA_FORK',
            description: 'Fork of tower-qa to deploy',
            defaultValue: 'ansible'
        )
        string(
            name: 'TOWER_QA_BRANCH',
            description: 'Branch to use for tower-qa',
            defaultValue: 'devel'
        )
        string(
            name: 'TOWERKIT_FORK',
            description: 'Fork of towerkit to deploy',
            defaultValue: 'ansible'
        )
        string(
            name: 'TOWERKIT_BRANCH',
            description: 'Branch to use for towerkit',
            defaultValue: 'devel'
        )
        booleanParam(
            name: 'BUILD_INSTALLER_AND_PACKAGE',
            description: 'Should the installer and the packages be built as part of this pipeline ?',
            defaultValue: true
        )
        choice(
            name: 'PACKAGE_TYPE',
            description: 'Which package type would you like to build ?',
            choices: ['rpm', 'deb']
        )
        booleanParam(
            name: 'RUN_INSTALLER',
            description: 'Should the installer be run as part of this pipeline ?',
            defaultValue: true
        )
        booleanParam(
            name: 'RUN_TESTS',
            description: 'Should the integration test suite be run as part of this pipeline ?',
            defaultValue: true
        )
        booleanParam(
            name: 'RUN_E2E',
            description: 'Should the e2e test suite be run as part of this pipeline ?',
            defaultValue: true
        )
        string(
            name: 'TESTEXPR',
            description: 'Specify the TESTEXPR to pass to pytest if necessary',
            defaultValue: ''
        )
        string(
            name: 'PYTEST_MP_PROCESSES',
            description: 'Number of processes to use for pytest',
            defaultValue: '4'
        )
        choice(
            name: 'PLATFORM',
            description: 'The OS to install the Tower instance on',
            choices: ['rhel-7.6-x86_64', 'rhel-7.5-x86_64', 'rhel-7.4-x86_64',
                      'ol-7.6-x86_64', 'centos-7.latest-x86_64',
                      'ubuntu-16.04-x86_64', 'ubuntu-14.04-x86_64']
        )
        choice(
            name: 'ANSIBLE_NIGHTLY_BRANCH',
            description: 'The Ansible version to install the Tower instance with',
            choices: ['devel', 'stable-2.7', 'stable-2.6', 'stable-2.5', 'stable-2.4', 'stable-2.3']
        )
    }

    options {
        timestamps()
    }

    stages {
        stage('Build Information') {
            steps {
                echo "TODO: Show Build Information here"
                script {
                    if (params.TOWER_BRANCH == 'devel' and params.TOWER_PACKAGING_BRANCH == 'devel') {
                        NIGHTLY_REPO_DIR = 'devel'
                    } else {
                        NIGHTLY_REPO_DIR = "tower-${params.TOWER_BRANCH}-packaging-${params.TOWER_PACKAGING_BRANCH}"
                    }
            }
        }

        stage('Build Installer') {
            when {
                expression {
                    return params.BUILD_INSTALLER_AND_PACKAGE
                }
            }

            steps {
                build(
                    job: 'Build_Tower_TAR',
                    parameters: [
                        string(
                            name: 'TOWER_PACKAGING_REPO',
                            value: "git@github.com:${params.TOWER_PACKAGING_FORK}/tower-packaging.git"
                        ),
                        string(
                            name: 'TOWER_PACKAGING_BRANCH',
                            value: "origin/${params.TOWER_PACKAGING_BRANCH}"
                        ),
                        string(
                            name: 'TOWER_REPO',
                            value: "git@github.com:${params.TOWER_FORK}/${params.PRODUCT}.git"
                        ),
                        string(
                            name: 'TOWER_BRANCH',
                            value: "origin/${params.TOWER_BRANCH}"
                        ),
                        string(
                            name: 'NIGHTLY_REPO_DIR',
                            value: NIGHTLY_REPO_DIR
                        )
                    ]
                )
            }
        }

        stage('Build Package') {
            when {
                expression {
                    return params.BUILD_INSTALLER_AND_PACKAGE
                }
            }

            steps {
                script {
                    if (params.PACKAGE_TYPE == 'rpm') {
                        PACKAGE_JOB_NAME = 'Build_Tower_RPM'
                    } else {
                        PACKAGE_JOB_NAME = 'Build_Tower_DEB'
                    }

                    build(
                        job: PACKAGE_JOB_NAME,
                        parameters: [
                            string(
                                name: 'TOWER_PACKAGING_REPO',
                                value: "git@github.com:${params.TOWER_PACKAGING_FORK}/tower-packaging.git"
                            ),
                            string(
                                name: 'TOWER_PACKAGING_BRANCH',
                                value: "origin/${params.TOWER_PACKAGING_BRANCH}"
                            ),
                            string(
                                name: 'TOWER_REPO',
                                value: "git@github.com:${params.TOWER_FORK}/${params.PRODUCT}.git"
                            ),
                            string(
                                name: 'TOWER_BRANCH',
                                value: "origin/${params.TOWER_BRANCH}"
                            ),
                            string(
                                name: 'NIGHTLY_REPO_DIR',
                                value: NIGHTLY_REPO_DIR
                            ),
                            booleanParam(
                                name: 'TRIGGER',
                                value: false
                            )
                        ]
                    )
                }
            }
        }

        stage('Install Tower') {
            when {
                expression {
                    return params.RUN_INSTALLER
                }
            }

            steps {
                script {
                    if (params.SCENARIO == 'standalone') {
                        INSTALL_JOB_NAME='Test_Tower_Install_Plain'
                    } else {
                        INSTALL_JOB_NAME='Test_Tower_Install_Cluster_Plain'
                    }

                    install_build = build(
                        job: INSTALL_JOB_NAME,
                        parameters: [
                            string(
                                name: 'INSTANCE_NAME_PREFIX',
                                value: "yolo-build-${env.BUILD_ID}"
                            ),
                            string(
                                name: 'AW_REPO_URL',
                                value: "${AWX_NIGHTLY_REPO_URL}/${NIGHTLY_REPO_DIR}"
                            ),
                            string(
                                name: 'TOWERQA_GIT_BRANCH',
                                value: "origin/${params.TOWER_QA_BRANCH}"
                            ),
                            string(
                                name: 'PLATFORM',
                                value: "${params.PLATFORM}"
                            ),
                            string(
                                name: 'ANSIBLE_NIGHTLY_BRANCH',
                                value: "${params.ANSIBLE_NIGHTLY_BRANCH}"
                            ),
                            booleanParam(
                                name: 'TRIGGER',
                                value: false
                            )
                        ]
                    )
                    TOWER_INSTALL_BUILD_ID = install_build.getId()
                }
            }
        }

        stage('Test Tower Integration') {
            when {
                expression {
                    return params.RUN_TESTS
                }
            }

            steps {
                script {
                    if (params.SCENARIO == 'standalone') {
                        INTEGRATION_JOB_NAME='Test_Tower_Integration_Plain'
                    } else {
                        INTEGRATION_JOB_NAME='Test_Tower_Integration_Cluster_Plain'
                    }

                    build(
                        job: INTEGRATION_JOB_NAME,
                        parameters: [
                            string(
                                name: 'TESTEXPR',
                                value: params.TESTEXPR
                            ),
                            string(
                                name: 'TEST_TOWER_INSTALL_BUILD',
                                value: TOWER_INSTALL_BUILD_ID
                            ),
                            booleanParam(
                                name: 'DESTROY_TEST_INSTANCE',
                                value: false
                            ),
                            string(
                                name: 'TOWERQA_GIT_BRANCH',
                                value: "origin/${params.TOWER_QA_BRANCH}"
                            ),
                            string(
                                name: 'TOWERKIT_GIT_BRANCH',
                                value: params.TOWERKIT_BRANCH
                            ),
                            string(
                                name: 'PLATFORM',
                                value: params.PLATFORM
                            ),
                            string(
                                name: 'ANSIBLE_NIGHTLY_BRANCH',
                                value: params.ANSIBLE_NIGHTLY_BRANCH
                            ),
                            string(
                               name: 'PYTEST_MP_PROCESSES',
                               value: params.PYTEST_MP_PROCESSES
                            )
                        ]
                    )
                }
            }
        }

        stage('Test Tower E2E') {
            when {
                expression {
                    return params.RUN_E2E
                }
            }

            steps {
                script {
                    if (params.SCENARIO == 'standalone') {
                        INSTALL_JOB_NAME = 'Test_Tower_Install_Plain'
                    } else {
                        INSTALL_JOB_NAME = 'Test_Tower_Install_Cluster_Plain'
                    }

                    copyArtifacts(
                        projectName: INSTALL_JOB_NAME,
                        filter: '.tower_url',
                        fingerprintArtifacts: true,
                        flatten: true,
                        selector: specific(TOWER_INSTALL_BUILD_ID)
                    )

                    script {
                        AWX_E2E_URL = readFile '.tower_url'
                    }

                    echo "Running e2e tests against ${AWX_E2E_URL}"

                    retry(2) {
                        build(
                            job: 'Test_Tower_E2E',
                            parameters: [
                                string(
                                    name: 'AWX_E2E_URL',
                                    value: "https://${AWX_E2E_URL}"
                                ),
                                string(
                                    name: 'TOWER_REPO',
                                    value: "git@github.com:${params.TOWER_FORK}/${params.PRODUCT}.git"
                                ),
                                string(
                                    name: 'TOWER_BRANCH_NAME',
                                    value: params.TOWER_BRANCH
                                )
                            ]
                        )
                    }
                }
            }
        }
    }

}
