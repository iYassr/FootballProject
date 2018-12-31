# Football Clubs

This website is part of Udacity FSND. 

## Getting Started

Following these instuctions will get you the website up and running. 

### Coding Style

pip8

### Installation
1.  Install VirtualBox  
You can download it from here (Linux, Windows, OSX ) https://www.virtualbox.org/wiki/Download_Old_Builds_5_1  
2. Install Vagrant  
You can Download it from here (Linux, Windows, OSX)  
https://www.vagrantup.com/downloads.html  
to check if vagrant is succeffully installed, please run  
`$ vagrant --versoin` from the command line  
3.  Download VM Configurations    
`$ git clone https://github.com/udacity/fullstack-nanodegree-vm.git  # clone git repository  
`  
4.  Download the Football Club Project( THIS )   
`$ git clone https://github.com/iYassr/FootballClub.git`  
move folder 'FootballClub' into ' the cloned folder 'vagrant' - step 4 -   

6. Run Vagrant Instance and SSH to it  
```
$ cd vagrant # cd to the cloned project folder  
$ vagrant up # wait until finished, it might take more that few minitus  
$ vagrant ssh # ssh to the already configured vm  
$ cd /vagrant  
```

### Running 
```
$ vagrant ssh               # ssh to the already initilized vagrant instance
$ cd /vagrant/FootballProject # cd into the projct folder
$ python3 project.py           # run the program
```


### ScreenShots


## JSON API Endpoints 

### JSON APIs to view Players Information
`url:port/Club/<int:club_id>/player/JSON`

### JSON APIs to view player Information
`url:port/Club/<int:club_id>/player/<int:player_id>/JSON`

### JSON APIs to view list all clubs
`url:port/Club/JSON`

## Author

iYassr

## Acknowledgment

Thanks MiSK and Udacity for this amazing course.

