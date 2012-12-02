echo "Tar started"
tar zvcf code.tar.gz *
echo "Tar completed"
echo "Copying tar to EC2"
scp -i ~/skreenkey.pem code.tar.gz ubuntu@107.20.241.50:/home/ubuntu/
echo "Copied tar to EC2"
echo "Untar started"
ssh -i ~/skreenkey.pem ubuntu@107.20.241.50 'cd /home/ubuntu; rm -fr splitscreen; mkdir splitscreen; mv code.tar.gz splitscreen; cd splitscreen; tar zvxf code.tar.gz; rm -fr code.tar.gz; find . -type f | xargs grep -l "localhost:5000" | xargs sed -i "s/localhost:5000/107\.20\.241\.50/g"; find . -type f | xargs grep -l "/home/shobit" | xargs sed -i "s/home\/shobit/home\/ubuntu/g"; '
echo "Untar completed. App is serving"
