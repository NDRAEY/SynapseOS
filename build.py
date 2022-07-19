import os, shutil, sys, tarfile, time, glob

CC = "clang -target i386-pc-none-elf -w -mno-sse -mno-avx -O0 -ffreestanding -I kernel/include/ -c"
SRC_TARGETS = []
BIN_TARGETS = []


def compile_kernel():
    print("Compiling...")
    shutil.rmtree(".\\bin\kernel\\", ignore_errors=True)
    os.mkdir(".\\bin\kernel\\")
    for i in range(0, len(SRC_TARGETS)):
        start_time = time.time()
        BIN_TARGETS.append(os.path.join("bin\\", os.path.basename(SRC_TARGETS[i]) + '.o '  ))
        os.system(f"echo {CC} -o {BIN_TARGETS[i]} {SRC_TARGETS[i]} & {CC} -o ./{BIN_TARGETS[i]} {SRC_TARGETS[i]} ")


def link_kernel():
    print("Linking...")
    print(f"BIN_TARGETS = {BIN_TARGETS}")
    os.system("ld.lld -T kernel/link.ld -nostdlib -o isodir/boot/kernel.elf " + ''.join(BIN_TARGETS))

def build_kernel():
    print("Building kernel", os.getcwd(), os.listdir())
    start_time = time.time()

    files = glob.glob("kernel/**/*.c", recursive=True) + glob.glob("kernel/**/*.s", recursive=True)

    for i in files:
        SRC_TARGETS.append(i)
    
    compile_kernel()
    link_kernel()
    x = 0
    while not os.path.exists("isodir/boot/kernel.elf"):
        x += 1
        compile_kernel()
        link_kernel()
        print(f"Errors: {x}")
    print(f"Build end at: {time.time() - start_time}")



def build_apps():
    os.chdir("apps/")
    os.system("python build.py")

    shutil.rmtree("../initrd/apps", ignore_errors=True)
    shutil.copytree("../bin/apps", "../initrd/apps")

    os.chdir("../initrd")
        

    with tarfile.open("../isodir/boot/initrd.tar", "w") as tar:
        for i in os.listdir():
            tar.add(i)
    os.chdir("../")


def create_iso():
    print("Creating ISO")
    start_time = time.time()

    if sys.platform == "linux" or sys.platform == "linux2":
        os.system("grub-mkrescue -o \"SynapseOS.iso\" isodir/ -V SynapseOS")
    else:
        os.system("ubuntu run grub-mkrescue -o \"SynapseOS.iso\" isodir/ -V SynapseOS ")
    
    print(f"Build end at: {time.time() - start_time}")


def create_iso_l():
    print("Creating ISO with limine")
    start_time = time.time()

    os.system("git clone https://github.com/limine-bootloader/limine.git --branch=v3.0-branch-binary --depth=1")
    os.system("make -C limine")
    os.system("mkdir -p iso_root")
    os.system("""cp -v isodir/boot/kernel.elf limine.cfg limine/limine.sys \
        limine/limine-cd.bin limine/limine-cd-efi.bin iso_root/
    """)
    os.system("""xorriso -as mkisofs -b limine-cd.bin \
          -no-emul-boot -boot-load-size 4 -boot-info-table \
          --efi-boot limine-cd-efi.bin \
          -efi-boot-part --efi-boot-image --protective-msdos-label \
          iso_root -o SynapseOS.iso""")
    os.system("./limine/limine-deploy SynapseOS.iso")
    
    print(f"Build end at: {time.time() - start_time}")


def run_qemu():
    if os.path.exists("ata.vhd"):
        pass
    else:
        os.system("qemu-img create -f raw ata.vhd 32M")
    
    qemu_command = "qemu-system-i386 -name SynapseOS -soundhw pcspk -m 16" \
        " -netdev socket,id=n0,listen=:2030 -device rtl8139,netdev=n0,mac=11:11:11:11:11:11 " \
        " -cdrom SynapseOS.iso -hda ata.vhd -serial  file:Qemu.log"
        
    os.system(
        qemu_command
        )


def run_qemu_debug():
    if os.path.exists("ata.vhd"):
        pass
    else:
        os.system("qemu-img create -f raw ata.vhd 32M")
    
    qemu_command = "qemu-system-i386 -name SynapseOS -soundhw pcspk -m 16" \
        " -netdev socket,id=n0,listen=:2030 -device rtl8139,netdev=n0,mac=11:11:11:11:11:11 " \
        " -cdrom SynapseOS.iso -hda ata.vhd -serial  file:Qemu.log" 
    print("gdb kernel.elf -ex target remote localhost:1234")
    os.system(
        qemu_command + """ -s -S"""
        )


if __name__ == "__main__":
    try:
        start_time = time.time()

        # Стандартная сборка
        
        if len(sys.argv) == 1:
            build_kernel()
            build_apps()
            create_iso()
            run_qemu()
        else:
            for i in range(1, len(sys.argv)):
                if sys.argv[i] == "kernel":
                    build_kernel()
                elif sys.argv[i] == "apps":
                    build_apps()
                elif sys.argv[i] == "isol":
                    create_iso_l()
                elif sys.argv[i] == "iso":
                    create_iso()
                elif sys.argv[i] == "run":
                    run_qemu()
                elif sys.argv[i] == "rund":
                    run_qemu_debug()
                else:
                    print(f"Ошибка, неизвестный аргумент: {sys.argv[i]}")
        print(f"Конец: {time.time() - start_time}")

    except Exception as E:
        print(E)