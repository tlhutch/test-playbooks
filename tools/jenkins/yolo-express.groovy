def TOWER_FORK
def TOWER_PACKAGING_FORK
def TOWER_BRANCH
def TOWER_PACKAGING_BRANCH
def NIGHTLY_REPO_DIR
def TOWER_QA_BRANCH
def TOWERKIT_BRANCH
def TEST_TOWER_INSTALL_BUILD_ID = 'lastBuild'
def PARALLELIZE = ''



stage ('Prepare Build') {
  node('jenkins-jnlp-agent') {
    
    def scmVars = checkout changelog: false, poll: false, scm: [$class: 'GitSCM', branches: [[name: '*/${TOWER_BRANCH}']], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'CloneOption', depth: 0, noTags: true, reference: '', shallow: true]], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'd2d4d16b-dc9a-461b-bceb-601f9515c98a', url: 'git@github.com:${TOWER_FORK}/${PRODUCT}.git']]]
    def commitHash = scmVars.GIT_COMMIT

    if (params.PARALLEL) {
      PARALLELIZE = '--mp --np 4'
      echo "Parallel forks set to ${params.PARALLEL}"
      } else {
        echo "Running tests in serial"
    }

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

    TOWERKIT_BRANCH_NAME = sh (
      returnStdout: true,
      script: 'echo ${TOWERKIT_BRANCH##*/}'
    ).trim()
    
    NIGHTLY_REPO_DIR = "${params.TOWER_BRANCH}-${commitHash}"
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
  node('jenkins-jnlp-agent') {
    if (params.RUN_INSTALLER) {
      install_build = build(
        job: 'qe-sandbox/Test_Tower_Install_Plain',
        parameters: [
          string(name: 'INSTANCE_NAME_PREFIX', value: "${params.CUSTOM_INSTANCE_PREFIX}"),
          string(name: 'AW_REPO_URL', value: "${AWX_NIGHTLY_REPO_URL}/${NIGHTLY_REPO_DIR}"),
          booleanParam(name: 'TRIGGER', value: false),
          string(name: 'TOWERQA_GIT_BRANCH', value: "origin/${TOWER_QA_BRANCH_NAME}"),
          string(name: 'PLATFORM', value: "${params.PLATFORM}"),
          string(name: 'ANSIBLE_NIGHTLY_BRANCH', value: "${params.ANSIBLE_NIGHTLY_BRANCH}")
        ]
      )

      TEST_TOWER_INSTALL_BUILD_ID = install_build.getId()
    } else {
      echo "Skipped installer"
    }
  }
}

stage('Test Tower Integration') {
  node('jenkins-jnlp-agent') {
    if (params.RUN_TESTS) {
      build(
        job: 'qe-sandbox/Test_Tower_Integration_Plain',
        parameters: [
          string(name: 'TESTEXPR', value: "${params.TESTEXPR}"),
          string(name: 'TEST_TOWER_INSTALL_BUILD', value: "${TEST_TOWER_INSTALL_BUILD_ID}"),
          booleanParam(name: 'DESTROY_TEST_INSTANCE', value: false),
          string(name: 'TOWERQA_GIT_BRANCH', value: "origin/${TOWER_QA_BRANCH_NAME}"),
          string(name: 'TOWERKIT_GIT_BRANCH', value: "${TOWERKIT_BRANCH_NAME}"),
          string(name: 'PLATFORM', value: "${params.PLATFORM}"),
          string(name: 'ANSIBLE_NIGHTLY_BRANCH', value: "${params.ANSIBLE_NIGHTLY_BRANCH}")
        ]
      )
    } else {
      echo "Skipped integration tests"
    }
  }
}
stage('Test Tower E2E') {
  node {
    if (params.RUN_E2E) {
      copyArtifacts(
        projectName: "qe-sandbox/Test_Tower_Install_Plain",
        filter: '.tower_url',
        fingerprintArtifacts: true,
        flatten: true,
        selector: specific(TEST_TOWER_INSTALL_BUILD_ID)
      )
      script {
        AWX_E2E_URL = readFile '.tower_url'
      }
      echo "Running e2e tests against ${AWX_E2E_URL}"
      retry(2) {
        build(
          job: 'Test_Tower_E2E',
          parameters: [
            string(name: 'AWX_E2E_URL', value: "https://${AWX_E2E_URL}"),
            string(name: 'TOWER_REPO', value: "git@github.com:${params.TOWER_FORK}/${params.PRODUCT}.git"),
            string(name: 'TOWER_BRANCH_NAME', value: "${TOWER_BRANCH_NAME}")
          ]
        )
      }
    } else {
      echo "Skipped E2E tests"
    }
  }
}
