echo "######################################################"
echo "Create virtual environment for flask app ..."
echo "######################################################"
# Step 1 - Initiate the application on AWS instance in virtual environment
python3 -m venv venv
. venv/bin/activate

# Step 2 Dependencies/Libraries Install
echo "######################################################"
echo Starting Installation of Dependencies Required for the Application ... 
echo "######################################################"
#Exit when error
set -e

pip3 install -r requirements.txt

echo "Done Installing Dependencies" 
