import React, { useState } from 'react';
import './index.scss';
import Layout from './Layout';
import { CssBaseline } from '@material-ui/core';

function App() {
  const [html, setHtml]   = useState();
  const [error, setError] = useState();

  const upload = (doc) => {
    setError(null);
    const body = new FormData();
    body.append('doc', doc);
    const url     = 'http://localhost:5000/doc2htmlByBLob';
    const options = {
      method: 'POST', body
    };
    fetch(url, options)
      .then(r => {
        if (!r.ok) {
          throw new Error(r.statusText);
        }
        return r.text();
      })
      .then(setHtml)
      .catch((e) => {
        setError(e.message);
        setHtml('');
      });
  };

  return (
    <>
      <CssBaseline />
      <Layout upload={upload} html={html} error={error} />
    </>
  );
}

export default App;
