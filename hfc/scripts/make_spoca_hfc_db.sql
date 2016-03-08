--
-- Table structure for table `FRC_INFO`
--

DROP TABLE IF EXISTS `FRC_INFO`;
CREATE TABLE `FRC_INFO` (
  `ID_FRC_INFO` integer primary key, -- Primary id
  `INSTITUT` text, -- Institute responsible for running the FR code
  `CODE` text, -- Name of the FR code
  `VERSION` text, -- Version of the FR code
  `FEATURE_NAME` text, -- Features detected
  `TARGET_NAME` text, -- Standard name of target
  `TARGET_CLASS` text, -- Type of target
  `ENC_MET` text, -- Encoding method (raster, chain code, none...)
  `PERSON` text, -- Person responsible for running the FR code
  `CONTACT` text, -- Contact of the person responsible for running the FR code
  `REFERENCE` text, -- Any reference to a document or article that describes the fr code
  `URL` text -- URL of a web site or document related to the FRC.
);

--
-- Table structure for table `OBSERVATORY`
--

DROP TABLE IF EXISTS `OBSERVATORY`;
CREATE TABLE `OBSERVATORY` (
  `ID_OBSERVATORY` integer primary key, -- Primary id
  `OBSERVAT` text, -- 'Name of the observatory/spacecraft',
  `INSTRUME` text, -- 'Name of the instrument',
  `TELESCOP` text, -- 'Name of the sub-part (telescope/receiver)',
  `OBSINST_KEY` text, -- 'HELIO ICS keyword of the observatory-instrument',
  `UNITS` text, -- 'Intensity units on the original observation',
  `WAVEMIN` real, -- 'Minimum wavelength of the observation',
  `WAVEMAX` real, -- 'Maximum wavelength of the observation',
  `WAVENAME` text, -- 'Name of the wavelength of the observation',
  `WAVEUNIT` text, -- 'Units of the wavelength of the observation',
  `FREQMIN` real, -- 'Minimum frequency of the observation',
  `FREQMAX` real, -- 'Maximum frequency of the observation',
  `FREQUNIT` text, -- 'Units of the frequency of the observation',
  `SPECTRAL_DOMAIN` text, -- 'Spectral domain covered by the observation',
  `OBS_TYPE` text, -- Type of observations (i.e., REMOTE-SENSING, IN-SITU, or BOTH)',
  `OBS_CAT` text, -- Category of observatory (i.e, SPACEBORNE, GROUND-BASED, or BOTH)',
  `COMMENT` text -- Any additional comment',
);

--
-- Table structure for table `PROCESSING_HISTORY`
--

DROP TABLE IF EXISTS `PROCESSING_HISTORY`;
CREATE TABLE `PROCESSING_HISTORY` (
  `ID` integer primary key, -- Primary id
  `OBSERVATORY_ID` integer, -- Pointing to ID_OBSERVATORY in OBSERVATORY table
  `FRC_INFO_ID` integer, -- Pointing to ID_FRC_INFO in FRC_INFO table
  `DATE_OBS` text, -- Date and time of observation
  `FILE_ID` text, -- Id of the data fileset
  `MAP_FILE` text, -- Name of the output feature map file
  `INIT_FILE` text, -- Name of the init. output file
  `FEAT_FILE` text, -- Name of the feat. output file
  `TRACK_FILE` text, -- Name of the track. output file
  `FEAT_RUN_DATE` text, -- Date and time when the fr code was run
  `TRACK_RUN_DATE` text, -- Date and time when the tracking code was run
  `STATUS`  text, -- Processing status
  `COMMENT` text, -- Comment on the last processing status
  FOREIGN KEY(OBSERVATORY_ID) REFERENCES OBSERVATORY(ID_OBSERVATORY),
  FOREIGN KEY(FRC_INFO_ID) REFERENCES FRC_INFO(ID_FRC_INFO)
);