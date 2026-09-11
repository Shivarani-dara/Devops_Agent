pipeline {
    agent any

    stages {

        stage('Install Dependencies') {
            steps {
                sh 'python3 -m pip install -r requirements.txt'
            }
        }

        stage('Run Tests') {
            steps {
                sh 'python3 -m pytest tests/nonexist.py'
            }
        }

        stage('Docker Build') {
            steps {
                sh 'docker build -t devops-agent-test .'
            }
        }
    }
}
