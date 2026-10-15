#include "kernel/types.h"
#include "kernel/stat.h"
#include "user/user.h"
static void fail(char *s) { printf("BENCH FAIL %s\n",s); exit(1); }
static void spin(int n) { volatile uint64 x=1; for(int i=0;i<n;i++) x=x*1664525+1013904223; }
int main(void) {
  int status, start, p[2];
  char *m=sbrk(16*1024*1024);
  if(m==(char*)-1) fail("sbrk");
  for(int i=0;i<16*1024*1024;i+=4096) m[i]=17;
  start=uptime();
  for(int j=0;j<200;j++) {
    int pid=fork(); if(pid<0) fail("fork");
    if(pid==0) { if(m[4096]!=17) fail("shared read"); m[4096]=29; if(m[4096]!=29) fail("write"); exit(0); }
    if(wait(&status)<0 || status!=0 || m[4096]!=17) fail("isolation");
  }
  printf("BENCH fork %d\n",uptime()-start);
  if(pipe(p)<0) fail("pipe");
  int pid=fork(); if(pid<0) fail("fork pipe");
  if(pid==0) {close(p[0]);write(p[1],"Z",1);exit(0);}
  close(p[1]); if(read(p[0],m,1)!=1 || m[0]!='Z')fail("copyout");close(p[0]);wait(&status);
  sbrk(-16*1024*1024);
  start=uptime();
  for(int j=0;j<4;j++) {pid=fork();if(pid<0)fail("cpu fork");if(!pid){spin(320000000);exit(0);}}
  for(int j=0;j<4;j++)if(wait(&status)<0||status)fail("cpu wait");
  printf("BENCH cpu %d\n",uptime()-start);
  start=uptime();
  for(int j=0;j<4;j++){pid=fork();if(pid<0)fail("mixed fork");if(!pid){for(int k=0;k<20;k++){spin(200000);pause(1);}exit(0);}}
  for(int j=0;j<4;j++)if(wait(&status)<0||status)fail("mixed wait");
  printf("BENCH mixed %d\n",uptime()-start);
  printf("BENCH correctness PASS\n");exit(0);
}
