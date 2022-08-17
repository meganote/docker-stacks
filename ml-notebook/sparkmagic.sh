#!/bin/bash
################################################################################
# Set sparkmagic config
################################################################################
livyConf=~/.sparkmagic/config.json
livyServer=${LIVY_SERVER:-"localhost:8998"}

# generate sparkmagic config
function sparkMagicConf() {
    python - <<=EOM
    
import json
import os
with open('${livyConf}.template', 'r') as template_json:
    data = json.loads(template_json.read())
data['kernel_python_credentials']['url']="$livyServer"
data['kernel_scala_credentials']['url']="$livyServer"
data['kernel_r_credentials']['url']="$livyServer"

env_dist = os.environ
for key in env_dist:
  if key.startswith('SPARK_PARA_CONF_'):
    configKey = key.replace('SPARK_PARA_CONF_', '', 1)
    configKey = configKey.replace('_', '.')
    data['session_configs']['conf'][configKey] = env_dist[key]

print(json.dumps(data))
=EOM
}

# Main
sparkMagicConf > $livyConf
