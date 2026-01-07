#include <errno.h>

#include "core/debug.h"
#include "core/emu.h"
#include "core/mem.h"
#include "core/mmu.h"
#include "core/usblink_queue.h"
#include "core/gif.h"

void gui_do_stuff(bool wait)
{
}

void do_stuff(int i)
{
}

void gui_debug_printf(const char *fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);

    gui_debug_vprintf(fmt, ap);

    va_end(ap);
}

void gui_debug_vprintf(const char *fmt, va_list ap)
{
    vprintf(fmt, ap);
}

void gui_status_printf(const char *fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);

    gui_debug_vprintf(fmt, ap);

    putchar('\n');

    va_end(ap);
}

void gui_perror(const char *msg)
{
    gui_debug_printf("%s: %s\n", msg, strerror(errno));
}

void gui_debugger_entered_or_left(bool entered) {}

void gui_debugger_request_input(debug_input_cb callback)
{
    if(!callback) return;
    static char debug_in[40];
    fgets(debug_in, sizeof(debug_in), stdin);
    callback(debug_in);
}

void gui_putchar(char c) { putc(c, stdout); }
int gui_getchar() { return -1; }
void gui_set_busy(bool busy) {}
void gui_show_speed(double d) {}
void gui_usblink_changed(bool state) {}
void throttle_timer_off() {}
void throttle_timer_on() {}
void throttle_timer_wait(unsigned int usec) {}

static const char OPT_BOOT1[]              = "--boot1";
static const char OPT_FLASH[]              = "--flash";
static const char OPT_SNAPSHOT[]           = "--snapshot";
static const char OPT_RAMPAYLOAD[]         = "--rampayload";
static const char OPT_RAMPAYLOAD_ADDR[]    = "--rampayload-address";
static const char OPT_DEBUG_ON_START[]     = "--debug-on-start";
static const char OPT_DEBUG_ON_WARN[]      = "--debug-on-warn";
static const char OPT_PRINT_ON_WARN[]      = "--print-on-warn";
static const char OPT_DIAGS[]              = "--diags";
static const char OPT_RDBG_PORT[]          = "--rdbg-port";
static const char OPT_GDB_PORT[]           = "--gdb-port";
static const char OPT_WRITE_GIF[]          = "--write-gif";
static const char OPT_REALTIME[]           = "--realtime";
static const char OPT_HELP[]               = "--help";
static uint32_t default_rampayload_base = 0x10000000;

void show_help_menu(void)
{
	fprintf(stderr, "firebird-headless:\n");
	fprintf(stderr, "  %-24s Show this help menu\n", OPT_HELP);
	fprintf(stderr, "  %-24s Path to Boot1 image (required)\n", OPT_BOOT1);
	fprintf(stderr, "  %-24s Path to Flash image (required)\n", OPT_FLASH);
	fprintf(stderr, "  %-24s Path to snapshot image (optional)\n", OPT_SNAPSHOT);
	fprintf(stderr, "  %-24s Path to RAM payload (optional)\n", OPT_RAMPAYLOAD);
	fprintf(stderr, "  %-24s Address to load RAM payload at (default: 0x%x)\n",
	       OPT_RAMPAYLOAD_ADDR, default_rampayload_base);
	fprintf(stderr, "  %-24s Enter debugger on start\n", OPT_DEBUG_ON_START);
	fprintf(stderr, "  %-24s Enter debugger on warnings\n", OPT_DEBUG_ON_WARN);
	fprintf(stderr, "  %-24s Print warnings to console\n", OPT_PRINT_ON_WARN);
	fprintf(stderr, "  %-24s Remote debugger port\n", OPT_RDBG_PORT);
	fprintf(stderr, "  %-24s GDB port\n", OPT_GDB_PORT);
	fprintf(stderr, "  %-24s Use diagnostics boot order\n", OPT_DIAGS);
	fprintf(stderr, "  %-24s Path to save GIF recording\n", OPT_WRITE_GIF);
	fprintf(stderr, "  %-24s Run in realtime (default: turbo mode)\n", OPT_REALTIME);
}

int main(int argc, char *argv[])
{
	const char *boot1 = nullptr, *flash = nullptr, *snapshot = nullptr, *rampayload = nullptr, *gif_filename = nullptr;
	bool help_menu = false;
	uint32_t rampayload_base = default_rampayload_base;
	unsigned int port_gdb = 0, port_rdbg = 0;

	turbo_mode = true;

	for(int argi = 1; argi < argc; ++argi)
	{
		if(strcmp(argv[argi], OPT_BOOT1) == 0)
			boot1 = argv[++argi];
		else if(strcmp(argv[argi], OPT_FLASH) == 0)
			flash = argv[++argi];
		else if(strcmp(argv[argi], OPT_SNAPSHOT) == 0)
			snapshot = argv[++argi];
		else if(strcmp(argv[argi], OPT_RAMPAYLOAD) == 0)
			rampayload = argv[++argi];
		else if(strcmp(argv[argi], OPT_RAMPAYLOAD_ADDR) == 0)
			rampayload_base = strtol(argv[++argi], nullptr, 0);
		else if(strcmp(argv[argi], OPT_DEBUG_ON_START) == 0)
			debug_on_start = true;
		else if(strcmp(argv[argi], OPT_DEBUG_ON_WARN) == 0)
			debug_on_warn = true;
		else if(strcmp(argv[argi], OPT_PRINT_ON_WARN) == 0)
			print_on_warn = true;
		else if(strcmp(argv[argi], OPT_DIAGS) == 0)
			boot_order = ORDER_DIAGS;
		else if(strcmp(argv[argi], OPT_RDBG_PORT) == 0)
			port_rdbg = strtol(argv[++argi], nullptr, 0);
		else if(strcmp(argv[argi], OPT_GDB_PORT) == 0)
			port_gdb = strtol(argv[++argi], nullptr, 0);
		else if(strcmp(argv[argi], OPT_WRITE_GIF) == 0)
			gif_filename = argv[++argi];
		else if(strcmp(argv[argi], OPT_REALTIME) == 0)
			turbo_mode = false;
		else if (strcmp(argv[argi], OPT_HELP) == 0)
			help_menu = true;
		else
		{
			fprintf(stderr, "Unknown argument '%s'.\n", argv[argi]);
			show_help_menu();
			return 1;
		}
	}

	if (argc == 1 || help_menu == true)
	{
		show_help_menu();
		return 1;
	}

	if(!boot1 || !flash)
	{
		fprintf(stderr, "You need to specify at least Boot1 and Flash images.\n");
		return 2;
	}

	path_boot1 = boot1;
	path_flash = flash;

	if(!emu_start(port_gdb, port_rdbg, snapshot))
		return 1;

	if(rampayload)
	{
		FILE *f = fopen(rampayload, "rb");
		if(!f)
		{
			perror("Could not open RAM payload");
			return 3;
		}

		fseek(f, 0, SEEK_END);
		size_t size = ftell(f);
		rewind(f);

		void *target = phys_mem_ptr(rampayload_base, size);
		if(!target)
		{
			fprintf(stderr, "RAM payload too big");
			return 5;
		}

		if(fread(target, size, 1, f) != 1)
		{
			perror("Could not read RAM payload");
			return 4;
		}

		fclose(f);

		// Jump to payload
		arm.reg[15] = rampayload_base;
	}

	if(gif_filename)
	{
		if(!gif_start_recording(gif_filename, 1))
		{
			fprintf(stderr, "Failed to start GIF recording to %s\n", gif_filename);
			return 6;
		}
	}

	emu_loop(false);

	if(gif_filename)
		gif_stop_recording();

	return 0;
}
