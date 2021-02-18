int oflash_dev_open(void)

{
  int __fd;
  int iVar1;
  int iVar2;
  
  __fd = open("/dev/oflash",2);
  iVar2 = __fd;
  if ((-1 < __fd) && (iVar1 = ioctl(__fd,0x40046f03,"ZkSe"), iVar1 != 0)) {
    iVar2 = -1;
    close(__fd);
  }
  return iVar2;
}

void oflash_dev_close(int param_1)

{
  if (param_1 < 0) {
    return;
  }
  close(param_1);
  return;
}


int oflash_read_data(uint param_1,undefined4 param_2,undefined4 param_3)

{
  int __fd;
  int iVar1;
  uint local_18;
  uint local_14;
  undefined4 uStack16;
  
  if ((param_1 == 0) ||
     (local_18 = param_1, local_14 = param_2, uStack16 = param_3, __fd = oflash_dev_open(), __fd < 0
     )) {
    iVar1 = -1;
  }
  else {
    local_18 = local_18 & 0xffff0000 | 0x1003;
    local_14 = param_1;
    iVar1 = ioctl(__fd,0x80086f04,&local_18);
    oflash_dev_close(__fd);
  }
  return iVar1;
}

