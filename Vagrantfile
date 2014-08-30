# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

    # Every Vagrant virtual environment requires a box to build off of.
    config.vm.box = "2creatives/vagrant-centos"
    config.vm.boot_timeout = 30

    # The url from where the 'config.vm.box' box will be fetched if it
    # doesn't already exist on the user's system.
    config.vm.box_url = "https://github.com/2creatives/vagrant-centos/releases/download/v6.5.3/centos65-x86_64-20140116.box"

    # SSH agent forwarding makes life easier
    config.ssh.forward_agent = true

    # Configure Salt stack
    config.vm.provision :salt do |config|
        config.install_type = 'stable'
    end

    # Define the vm
    vm_name = "botdev"
    config.vm.define :dev do |dev|
        dev.vm.network :private_network, ip: "172.30.30.30"
        dev.vm.hostname = vm_name

        dev.vm.synced_folder "salt/roots/", "/srv/"
        dev.vm.synced_folder ".",           "/src/"

        # dev.vm.network :forwarded_port, guest: 22, host: 22, auto_correct: true

        dev.vm.provider "virtualbox" do |v|
            v.name = vm_name
            v.customize ["modifyvm", :id, "--memory", "256"]
        end

        dev.vm.provision :salt do |config|
            config.minion_config = "salt/minion.conf"
            config.run_highstate = true
            config.verbose = true
            config.bootstrap_options = "-D"
            config.temp_config_dir = "/tmp"
        end
    end
end
