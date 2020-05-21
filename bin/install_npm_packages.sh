#!/bin/bash

# Navigate to the static resources directory
cd $(dirname "${BASH_SOURCE[0]}")
cd ../looking_glass/static

# References:
# https://docs.aws.amazon.com/sdk-for-javascript/v2/developer-guide/setting-up-node-on-ec2-instance.html
# https://github.com/nvm-sh/nvm/blob/master/README.md
# https://www.npmjs.com/package/vis-network
# https://stackoverflow.com/questions/24514936/how-can-i-serve-npm-packages-using-flask
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.35.3/install.sh | bash
. ~/.nvm/nvm.sh
nvm install node

npm install @egjs/hammerjs@2.0.17
npm install @types/hammerjs@2.0.36
npm install component-emitter@1.3.0
npm install keycharm@0.3.0
npm install moment@2.24.0
npm install timsort@0.3.0
npm install uuid@7.0.0
npm install vis-data@6.2.1
npm install vis-util@4.0.0
npm install vis-uuid@1.1.3
npm install vis-network@7.6.8
