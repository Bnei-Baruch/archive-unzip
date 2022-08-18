import React, {useState} from 'react';
import {
    FormControl,
    IconButton,
    Container,
    Box,
    FormHelperText,
    Input,
    Paper,
    Button,
    Grid,
    Typography,
    CircularProgress, Select, MenuItem,
} from '@material-ui/core';
import {FormatTextdirectionLToR, FormatTextdirectionRToL, Publish} from '@material-ui/icons';
import {ALL_LANGUAGES, LANG_HEBREW} from "./consts.mjs";

const dirEnum = {ltr: 'ltr', rtl: 'rtl'};
const defLang = localStorage.getItem('lang') || LANG_HEBREW;
const defDir = localStorage.getItem('dir') || dirEnum.ltr

const Layout = ({html, upload, error, wip}) => {
    const [doc, setDoc] = useState();
    const [file, setFile] = useState();
    const [dir, setDir] = useState(defDir);
    const [lang, setLang] = useState(defLang);

    const handleChangeLang = e => {
        const l = e.target.value;
        setLang(l);
        localStorage.setItem('lang', l)
    };

    const handleChangeDoc = ({target: {value, files}}) => {
        setDoc(value);
        files.length > 0 && setFile(files[0]);
    };

    const handleUpload = () => upload(file);

    const renderUpload = () => (
        <Grid container spacing={6} alignContent="center" alignItems="center">
            <Grid item xs={7}>
                <FormControl variant="outlined" fullWidth>
                    <Input
                        id="doc"
                        name="doc"
                        aria-describedby="forUploadFile"
                        type="file"
                        onChange={handleChangeDoc}
                    />
                    <FormHelperText id="forUploadFile">
                        <Typography color={error ? 'error' : 'primary'} component="span">
                            {error ? error : doc}
                        </Typography>
                    </FormHelperText>

                </FormControl>
            </Grid>
            <Grid item xs={5}>
                <IconButton
                    onClick={() => setDir(dir === dirEnum.ltr ? dirEnum.rtl : dirEnum.ltr)}
                    style={{'marginRight': '1em'}}
                >
                    {
                        dir === dirEnum.ltr
                            ? <FormatTextdirectionRToL/>
                            : <FormatTextdirectionLToR/>
                    }
                </IconButton>
                <Button
                    onClick={handleUpload}
                    variant="contained"
                    disabled={!file}
                >
                    Upload file
                    <Publish/>
                </Button>
                <FormControl variant="standard" sx={{m: 1}}>
                    <Select
                        id="langs-select"
                        value={lang}
                        label="Language"
                        onChange={handleChangeLang}
                    >
                        {ALL_LANGUAGES.map(l => <MenuItem value={l}>{l}</MenuItem>)}
                    </Select>
                </FormControl>
            </Grid>
        </Grid>
    );

    const renderPreview = () => (
        <div>
            <div className={`search-on-page--container ${lang}_styles`}>
                <div
                    style={{direction: dir, textAlign: (dir === dirEnum.ltr ? 'left' : 'right'), padding: '1em'}}
                    dangerouslySetInnerHTML={{__html: html}}
                />
            </div>
        </div>
    );

    const renderWip = () => {
        return (
            <Box style={{
                position: 'absolute',
                top: '0',
                bottom: '0',
                right: '0',
                left: '0',
                background: 'rgba(158, 158, 158, 0.5)',
                zIndex: '100',
                verticalAlign: 'middle',
                textAlign: 'center'
            }}>
                <CircularProgress style={{marginTop: '2em'}} size={60}/>
            </Box>
        );
    };

    return (
        <Container maxWidth="md">
            <Box m={2} style={{position: 'relative'}}>
                {wip && renderWip()}
                {renderUpload()}
            </Box>
            <Paper variant="outlined" style={{minHeight: '90vh'}}>
                {renderPreview()}
            </Paper>
        </Container>
    );
};

export default Layout;
