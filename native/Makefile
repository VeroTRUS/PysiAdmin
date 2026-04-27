CC     := gcc
CFLAGS := -O2 -Wall -Wextra -std=c11 -D_POSIX_C_SOURCE=200809L -fPIC

TARGET_SYSINFO := sysinfo
TARGET_LIB     := libpysiasm.so

ARCH := $(shell uname -m)

ifeq      ($(ARCH),x86_64)
    ASM_SRC := asm/x86_64.S
else ifeq ($(ARCH),aarch64)
    ASM_SRC := asm/arm64.S
else ifeq ($(ARCH),ppc64le)
    ASM_SRC := asm/powerpc64.S
else ifeq ($(ARCH),riscv64)
    ASM_SRC := asm/riscv64.S
else ifeq ($(ARCH),s390x)
    ASM_SRC := asm/s390x.S
else
    $(warning Unsupported arch $(ARCH) -- libpysiasm.so will not be built)
    ASM_SRC :=
endif

.PHONY: all clean

all: $(TARGET_SYSINFO) $(if $(ASM_SRC),$(TARGET_LIB))

$(TARGET_SYSINFO): sysinfo.c
	$(CC) $(CFLAGS) -o $@ $<

$(TARGET_LIB): asm_wrapper.c $(ASM_SRC)
	$(CC) $(CFLAGS) -shared -o $@ $^

clean:
	rm -f $(TARGET_SYSINFO) $(TARGET_LIB)
