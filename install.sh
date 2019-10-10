mkdir PTO
wget https://raw.githubusercontent.com/FurqanKhan1/Dictator/master/nmapscan.sql
cd PTO
apt-get install python-mysqldb
pip install pymetasploit --proxy=http://proxy-us.intel.com:912
wget https://raw.githubusercontent.com/FurqanKhan1/Dictator/master/nmapscan.sql
git clone https://github.com/FurqanKhan1/Dictator.git
git clone https://github.com/FurqanKhan1/Dictator_client.git
apt-get install mdns-scan
pip install python-nmap --proxy=http://proxy-us.intel.com:912
pip install python-libnmap --proxy=http://proxy-us.intel.com:912
pip install python-libnessus --proxy=http://proxy-us.intel.com:912
pip install lxml --proxy=http://proxy-us.intel.com:912
pip install psutil --proxy=http://proxy-us.intel.com:912
pip install django==1.11.10 --proxy=http://proxy-us.intel.com:912
pip install djangorestframework==3.7.7 --proxy=http://proxy-us.intel.com:912
pip install markdown  --proxy=http://proxy-us.intel.com:912     # Markdown support for the browsable API. 
pip install django-filter --proxy=http://proxy-us.intel.com:912# Filtering support
sudo apt-get install python-mysqldb
apt-get install python-magic
pip install texttable --proxy=http://proxy-us.intel.com:912
pip install pyshark==0.3.8 --proxy=http://proxy-us.intel.com:912
pip install ansi2html --proxy=http://proxy-us.intel.com:912
cd dictator_service/Dictator_service/Scripts/hoppy-1.8.1/hoppy-1.8.1-
sudo make install
cd ..
git clone https://github.com/EnableSecurity/sipvicious.git
cd sipvicious
python setup.py install --proxy=http://proxy-us.intel.com:912
cd ..
service mysql stop
apt-get --purge remove 'mysql*'
mkdir mysql_install
cd mysql_install
wget https://dev.mysql.com/get/Downloads/mysql/mysql-server_5.7.17-1debian7_amd64.deb-bundle.tar
tar -xvf mysql-server_5.7.17-1debian7_amd64.deb-bundle.tar
sudo dpkg-preconfigure mysql-community-server_*.deb
sudo apt-get install libaio1
sudo dpkg -i mysql-{common,community-client,client,community-server,server}_*.deb
sudo apt-get -f install
apt-get install python-mysqldb
#sudo apt-get update
cd ..
service mysql start
mysql -p  < nmapscan.sql
