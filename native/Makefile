CC      := gcc
CFLAGS  := -O2 -Wall -Wextra -std=c11 -D_POSIX_C_SOURCE=200809L
TARGET  := sysinfo

.PHONY: all clean

all: $(TARGET)

$(TARGET): sysinfo.c
	$(CC) $(CFLAGS) -o $@ $

clean:
	rm -f $(TARGET)
