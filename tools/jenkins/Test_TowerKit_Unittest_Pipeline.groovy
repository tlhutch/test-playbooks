pipeline {
    agent {
        label 'jenkins-jnlp-agent'
    }
    options {
        timeout(time: 1, unit: 'HOURS')
        timestamps()
    }
    stages {
        stage('Checkout SCM') {
            failFast true
            parallel {
                stage('Checkout tower-qa') {
                  steps {
                    checkout([$class: 'GitSCM', branches: [[name: '*/master']], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: 'tower-qa']], submoduleCfg: [], userRemoteConfigs: [[credentialsId: '55b638c7-3ef3-4679-9020-fa09e411a74d', url: 'https://github.com/ansible/tower-qa.git']]])  
                  }
                }
                stage('Checkout towerkit') {
                  steps {
                    checkout([$class: 'GitSCM', branches: [[name: '*/master']], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: 'towerkit']], submoduleCfg: [], userRemoteConfigs: [[credentialsId: '55b638c7-3ef3-4679-9020-fa09e411a74d', url: 'https://github.com/ansible/towerkit']]])}
                }
            }
        }
        stage('Execute Shell Script') {
            steps {
                sh returnStdout: true, script: '''cd towerkit
                bash -xe ../tower-qa/tools/jenkins/scripts/Test_Towerkit_Unittest.sh'''
            }
        }
        stage('PyLint') {
            steps {
                warnings canComputeNew: false, canResolveRelativePaths: false, canRunOnFailed: true, categoriesPattern: '', consoleParsers: [[parserName: 'PyLint']], defaultEncoding: '', excludePattern: '', failedTotalAll: '0', healthy: '', includePattern: '', messagesPattern: '', unHealthy: ''
            }
        }
        stage('junit Report and Archive') {
            steps {
                junit healthScaleFactor: 0.0, keepLongStdio: true, testResults: '*/report.xml'
                archiveArtifacts '*/report.*'
            }
        }    
    }
}
