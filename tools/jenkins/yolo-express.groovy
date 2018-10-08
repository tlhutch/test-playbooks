def TOWER_FORK
def TOWER_PACKAGING_FORK
def TOWER_BRANCH
def TOWER_PACKAGING_BRANCH
def NIGHTLY_REPO_DIR
def TOWER_QA_BRANCH
def TEST_TOWER_INSTALL_BUILD_ID = 'lastBuild'

stage ('Prepare Build') {
  node('master') {
    TOWER_BRANCH_NAME = sh (
      returnStdout: true,
      script: 'echo ${TOWER_BRANCH##*/}'
    ).trim()

    TOWER_PACKAGING_BRANCH_NAME = sh (
      returnStdout: true,
      script: 'echo ${TOWER_PACKAGING_BRANCH##*/}'
    ).trim()

    TOWER_QA_BRANCH_NAME = sh (
      returnStdout: true,
      script: 'echo ${TOWER_QA_BRANCH##*/}'
    ).trim()

    NIGHTLY_REPO_DIR = "${params.TOWER_BRANCH}-${BUILD_ID}"
  }
}

stage('Build Tower') {
  parallel buildInstaller: {
    if (params.BUILD_INSTALLER) {
      build(
        job: 'Build_Tower_TAR',
        parameters: [
          string(name: 'TOWER_PACKAGING_REPO', value: "git@github.com:${params.TOWER_PACKAGING_FORK}/tower-packaging.git"),
          string(name: 'TOWER_REPO', value: "git@github.com:${params.TOWER_FORK}/${params.PRODUCT}.git"),
          string(name: 'TOWER_PACKAGING_BRANCH', value: "origin/${TOWER_PACKAGING_BRANCH_NAME}"),
          string(name: 'TOWER_BRANCH', value: "origin/${TOWER_BRANCH_NAME}"),
          string(name: 'NIGHTLY_REPO_DIR', value: NIGHTLY_REPO_DIR)
        ]
      )
    } else {
      echo "Skipped installer build"
    }
  }, buildRPM: {
    if (params.BUILD_RPM) {
      build(
        job: 'Build_Tower_RPM',
        parameters: [
          string(name: 'TOWER_PACKAGING_REPO', value: "git@github.com:${params.TOWER_PACKAGING_FORK}/tower-packaging.git"),
          string(name: 'TOWER_REPO', value: "git@github.com:${params.TOWER_FORK}/${params.PRODUCT}.git"),
          string(name: 'TOWER_PACKAGING_BRANCH', value: "origin/${TOWER_PACKAGING_BRANCH_NAME}"),
          string(name: 'TOWER_BRANCH', value: "origin/${TOWER_BRANCH_NAME}"),
          string(name: 'NIGHTLY_REPO_DIR', value: NIGHTLY_REPO_DIR),
          booleanParam(name: 'TRIGGER', value: false),
        ]
      )
    } else {
      echo "Skipped RPM build"
    }
  },
  failFast: true
}

stage('Install Tower') {
  node {
    if (params.RUN_INSTALLER) {
      install_build = build(
        job: 'Test_Tower_Install',
        parameters: [
          string(name: 'INSTANCE_NAME_PREFIX', value: "${params.CUSTOM_INSTANCE_PREFIX}"),
          string(name: 'AW_REPO_URL', value: "${AWX_NIGHTLY_REPO_URL}/${NIGHTLY_REPO_DIR}"),
          booleanParam(name: 'TRIGGER', value: false),
          [
            $class: 'MatrixCombinationsParameterValue',
            name: 'config',
            description: '',
            combinations: [
              'ANSIBLE_NIGHTLY_BRANCH=stable-2.6,PLATFORM=rhel-7.5-x86_64,label=jenkins-jnlp-agent'
            ],
          ]
        ]
      )

      TEST_TOWER_INSTALL_BUILD_ID = install_build.getId()
    } else {
      echo "Skipped installer"
    }
  }
}

stage('Test Tower') {
  node {
    if (params.RUN_TESTS) {
      build(
        job: 'Test_Tower_Integration_CA_Test',
        parameters: [
          string(name: 'TESTEXPR', value: "${params.TESTEXPR}"),
          string(name: 'TEST_TOWER_INSTALL_BUILD', value: "${TEST_TOWER_INSTALL_BUILD_ID}"),
          string(name: 'TOWERQA_GIT_BRANCH', value: "origin/${TOWER_QA_BRANCH_NAME}"),
          [
            $class: 'MatrixCombinationsParameterValue',
            name: 'config',
            description: '',
            combinations: [
              'ANSIBLE_NIGHTLY_BRANCH=stable-2.6,PLATFORM=rhel-7.5-x86_64,label=jenkins-jnlp-agent'
            ],
          ]
        ]
      )
    } else {
      echo "Skipped tests"
    }
  }
}