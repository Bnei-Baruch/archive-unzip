import React, { useContext, useEffect, useRef, useState } from 'react';
import { getLanguageDirection } from 'kmedia-mdb/src/helpers/i18n-utils';
import {
  FormControl,
  InputAdornment,
  IconButton,
  Container,
  Box,
  FormHelperText,
  InputLabel,
  Input,
  Paper,
  Button, ButtonBase, TextField, ButtonGroup, Grid, Typography
} from '@material-ui/core';
import { Publish } from '@material-ui/icons';

const Layout = ({ language = 'he', html, upload, error }) => {

  const [doc, setDoc]   = useState();
  const [file, setFile] = useState();
  const direction       = getLanguageDirection(language);

  const handleChangeDoc = ({ target: { value, files } }) => {
    setDoc(value);
    files.length > 0 && setFile(files[0]);
  };

  const handleUpload = () => upload(file);

  const renderUpload = () => (
    <Grid container spacing={6} alignContent="center" alignItems="center">
      <Grid item xs={9}>
        <FormControl variant="outlined" fullWidth>
          <Input
            id="doc"
            name="doc"
            aria-describedby="forUploadFile"
            type="file"
            onChange={handleChangeDoc}
          />
          <FormHelperText id="forUploadFile">
            <Typography color={error ? 'error' : 'primary'}>
              {error ? error : doc}
            </Typography>
          </FormHelperText>

        </FormControl>
      </Grid>
      <Grid xs={3}>

        <Button
          onClick={handleUpload}
          variant="contained"

        >
          Upload file
          <Publish />
        </Button>
      </Grid>
    </Grid>
  );

  const renderPreview = () => (
    <div>
      <div className="search-on-page--container">
        <div
          style={{ direction, textAlign: (direction === 'ltr' ? 'left' : 'right') }}
          dangerouslySetInnerHTML={{ __html: html }}
        />
      </div>
    </div>
  );

  return (
    <Container maxWidth="md">
      <Box m={2}>
        {renderUpload()}
      </Box>
      <Paper variant="outlined" style={{ minHeight: '90vh' }}>
        {renderPreview()}
      </Paper>
    </Container>
  );
};

export default Layout;
