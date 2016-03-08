; To compile the procedure in a runtime program, start a clean solar soft session with at least aia and onthology in your SSW_INSTR variable
; e.g. SSW_INSTR="ontology aia"
; Then once in the idl prompt, type the following commands, then exit
; .compile runtime_aia_prep
; resolve_all,  /CONTINUE_ON_ERROR
; save, /routines, filename="runtime_aia_prep.sav", DESCRIPTION="Runtime IDL program to call aia_prep on fits file", /verbose, /embedded

; For this procedure to run, the 3 following environement variables must be set
; SSW=/path/to/your/solar/soft
; SSW_ONTOLOGY=$SSW/vobs/ontology
; AIA_CALIBRATION=$SSW/sdo/aia/calibration
; N.B. Don't forget to export the variables


; Then to run the procedure, type the following command in a regular shell
; idl -queue -rt=runtime_aia_prep.sav -args outdir fitsfile1 fitsfile2 fitsfile3 ...
; N.B. The -queue says to wait for a license to be available


PRO runtime_aia_prep

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

PRINT, "About to aia_prep the following files: ", files


outfile=files+'.prep'
aia_prep, files, indgen(N_ELEMENTS(files)), /verbose, outdir=outdir, outfile=outfile, /do_write_fits

END

