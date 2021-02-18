
undefined4 main(void)

{
  undefined uVar1;
  FILE *__stream;
  int memfd;
  undefined4 uVar2;
  void *__addr;
  int iVar3;
  uint uVar4;
  unkbyte9 Var5;
  byte local_dc;
  undefined local_db;
  uchar *local_d8;
  undefined local_d4;
  undefined7 uStack211;
  undefined uStack204;
  uchar auStack196 [16];
  undefined4 local_b4;
  undefined4 local_b0;
  undefined4 local_ac;
  undefined4 local_a8;
  uint local_a4;
  uint uStack160;
  undefined local_94 [4];
  uint uStack144;
  undefined uStack140;
  undefined8 local_8a;
  uint local_3c;
  
  Var5 = SUB169(ZEXT816(0),0);
  local_3c = __stack_chk_guard;
  local_d4 = 0;
  uStack211 = 0;
  uStack204 = 0;
  memfd = open("/dev/mem",0x101002);
  if (memfd < 0) {
    puts("open /dev/mem fail");
  }
  else {
    __addr = mmap((void *)0x0,0x810,1,1,memfd,0x1c23000);
    if (__addr == (void *)0xffffffff) {
      puts("mmap fail");
      close(memfd);
    }
    else {
      local_b4 = *(undefined4 *)((int)__addr + 0x800);
      local_b0 = *(undefined4 *)((int)__addr + 0x804);
      local_ac = *(undefined4 *)((int)__addr + 0x808);
      local_a8 = *(undefined4 *)((int)__addr + 0x80c);
      munmap(__addr,0x810);
      close(memfd);
      dump_val(&local_b4,&DAT_000118d8,0x10);
      memfd = oflash_dev_open();
      if (-1 < memfd) {
        uVar1 = (undefined)Var5;
        uStack140 = (undefined)((unkuint9)Var5 >> 0x40);
        uVar2 = CONCAT22(CONCAT11(uStack140,uStack140),CONCAT11(uStack140,uStack140));
        local_94 = CONCAT31((int3)uVar2,uVar1);
        uStack144 = (uint)(CONCAT44(uVar2,uVar2) >> 0x18);
        uVar2 = CONCAT22(CONCAT11(uVar1,uVar1),CONCAT11(uVar1,uVar1));
        local_8a = CONCAT44(uVar2,uVar2);
        iVar3 = ioctl(memfd,0x80126f05,(MD5_CTX *)local_94);
        if (-1 < iVar3) {
          local_a4 = local_94;
          uStack160 = uStack144;
          oflash_dev_close(memfd);
          dump_val(&local_a4,&DAT_000118f4,8);
          oflash_read_data.constprop.0(&local_d4);
          dump_val(&local_d4,"bef secData",0x10);
          MD5_Init((MD5_CTX *)local_94);
          MD5_Update((MD5_CTX *)local_94,&local_b4,0x10);
          MD5_Update((MD5_CTX *)local_94,"zkswe_a33",9);
          MD5_Update((MD5_CTX *)local_94,&local_a4,8);
          MD5_Update((MD5_CTX *)local_94,"zkgame",6);
          uVar4 = 0;
          MD5_Final(auStack196,(MD5_CTX *)local_94);
          dump_val(auStack196,&DAT_00011916,0x10);
          __stream = stderr;
          memfd = oflash_dev_open();
          if (-1 < memfd) {
            local_dc = 0;
            iVar3 = ioctl(memfd,0x80016f01,&local_dc);
            fprintf(stderr,"ddd %d   rs  %x\n",iVar3,(uint)local_dc);
            iVar3 = ioctl(memfd,0x80016f01,&local_dc);
            if (iVar3 == 0) {
              uVar4 = ((uint)local_dc << 0x1d) >> 0x1f;
            }
            oflash_dev_close(memfd);
          }
          fprintf(__stream,"page is lock %d\n",uVar4);
          memfd = oflash_dev_open();
          if (memfd < 0) {
            iVar3 = -1;
          }
          else {
            local_dc = 3;
            local_db = 0x10;
            local_d8 = auStack196;
            iVar3 = ioctl(memfd,0x40086f04,&local_dc);
            oflash_dev_close(memfd);
          }
          fprintf(stderr,"write ret %d\n",iVar3);
          oflash_read_data.constprop.0(&local_d4);
          dump_val(&local_d4,"after secData",0x10);
          memfd = oflash_dev_open();
          if (-1 < memfd) {
            local_dc = 0x31;
            iVar3 = ioctl(memfd,0x40016f01);
            fprintf(stderr,"ret %d\n",iVar3);
            oflash_dev_close(memfd);
          }
          uVar2 = 0;
          goto LAB_000109b8;
        }
        puts("OFLASH_IOC_RD_DEVID < 0");
        oflash_dev_close(memfd);
      }
    }
  }
  uVar2 = 0xffffffff;
LAB_000109b8:
  if (local_3c == __stack_chk_guard) {
    return uVar2;
  }
                    /* WARNING: Subroutine does not return */
  __stack_chk_fail();
}

 
