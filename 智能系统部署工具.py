import os
import subprocess
import re
import logging

def run_command(command):
   
    try:
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
        logging.info("执行命令成功: %s", command)
        return output
    except subprocess.CalledProcessError as e:
        logging.error("命令执行失败: %s\n输出：%s", command, e.output)
        return None

def detect_harddisks():
   
    cmd = 'wmic diskdrive get Model,Size'
    output = run_command(cmd)
    disks = []
    if output:
       
        lines = output.splitlines()
    
        for line in lines[1:]:
            parts = re.split(r'\s{2,}', line.strip())
            if len(parts) >= 2:
                model = parts[0]
                try:
                    size = int(parts[1])
                except ValueError:
                    size = 0
                disks.append({'model': model, 'size': size})
    return disks

def generate_diskpart_script(disk_number):
   
    script = f"""
select disk {disk_number}
clean
convert gpt
create partition primary size=102400    // 创建系统分区（约100GB，可根据需要调整）
format quick fs=ntfs label="System"
assign letter=C
create partition primary                // 剩余空间作为数据分区
format quick fs=ntfs label="Data"
assign letter=D
exit
"""
    return script

def partition_disk(disk_number):
   
    script = generate_diskpart_script(disk_number)
    script_file = "diskpart_script.txt"
    with open(script_file, "w", encoding="utf-8") as f:
        f.write(script)
    logging.info("开始执行磁盘分区操作...")
    cmd = f"diskpart /s {script_file}"
    output = run_command(cmd)
    os.remove(script_file)
    return output

def apply_ghost_image(source_image, target_drive):

    cmd = f'ghost.exe -clone,mode=restore,src="{source_image}",dst="{target_drive}" -batch -sure'
    logging.info("开始部署Ghost镜像...")
    output = run_command(cmd)
    return output

def load_drivers():
    
    logging.info("加载驱动程序...")
    cmd = "driver_install.bat"
    output = run_command(cmd)
    return output

def deploy_system(disk_number, ghost_image_path, target_drive):
   
    logging.info("检测到需要操作的磁盘编号：%d", disk_number)
    
    partition_output = partition_disk(disk_number)
    logging.info("磁盘分区操作完成，输出：\n%s", partition_output)
    
    load_drivers()
    
    ghost_output = apply_ghost_image(ghost_image_path, target_drive)
    logging.info("Ghost镜像部署完成，输出：\n%s", ghost_output)
    

    logging.info("部署完成，即将重启系统...")
    #run_command("shutdown /r /t 0")

def batch_deploy(deployments):
    
    for task in deployments:
        deploy_system(task['disk_number'], task['ghost_image'], task['target_drive'])

if __name__ == "__main__":
    
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

    disks = detect_harddisks()
    logging.info("检测到的硬盘信息：%s", disks)

    deploy_system(disk_number=0, ghost_image_path="system.gho", target_drive="C:")
