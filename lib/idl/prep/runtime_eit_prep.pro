; To compile the procedure in a runtime program, start a clean solar soft session with at least eit and onthology in your SSW_INSTR variable
; e.g. SSW_INSTR="ontology eit"
; Then once in the idl prompt, type the following commands, then exit
; .compile runtime_eit_prep
; resolve_all,  /CONTINUE_ON_ERROR
; save, /routines, filename="runtime_eit_prep.sav", DESCRIPTION="Runtime IDL program to call eit_prep on fits file", /verbose, /embedded

; Then to run the procedure, type the following command in a regular shell
; idl -queue -rt=runtime_eit_prep.sav -args outdir fitsfile1 fitsfile2 fitsfile3 ...
; N.B. The -queue says to wait for a license to be available


PRO runtime_eit_prep

; This is supposed to avoid any error message on the screen 
Set_Plot, 'NULL'

args = COMMAND_LINE_ARGS(count=nargs)
IF nargs EQ 0 THEN BEGIN
	PRINT, "Error you must provide at least one fits file, exiting"
	RETURN
ENDIF

outdir = '.'
; If the first parameter is a writable directory, we set it as the outdir

IF FILE_TEST(args[0], /DIRECTORY, /WRITE) THEN BEGIN
	outdir = args[0]
	IF nargs EQ 1 THEN BEGIN
		PRINT, "Error you must provide at least one fits file, exiting"
		RETURN
	ENDIF ELSE files = args[1:*]
ENDIF ELSE files = args

PRINT, "About to eit_prep the following files: ", files

eit_prep, files, /verbose, outdir=outdir, /outfits, /no_prompt

END

