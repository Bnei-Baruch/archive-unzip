import React, { useState } from 'react';
import './index.scss';
import Layout from './Layout';
import { CssBaseline } from '@material-ui/core';

function App() {
  const [html, setHtml]   = useState();
  const [error, setError] = useState();
  const [wip, setWip]     = useState(false);

  const upload = (doc) => {
    setWip(true);
    setHtml('');
    setError(null);
    const body = new FormData();
    body.append('doc', doc);

    const url = `${process.env.REACT_APP_BACKEND}doc2htmlByBLob`;

    const options = { method: 'POST', body };
    fetch(url, options)
      .then(r => {
        if (!r.ok) {
          throw new Error(r.statusText);
        }
        return r.json();
      })
      .then((d) => setHtml(d.html))
      .catch((e) => {
        setError(e.message);
      }).finally(() => setWip(false));
  };

  return (
    <>
      <CssBaseline />
      <Layout upload={upload} html={html} error={error} wip={wip} />
    </>
  );
}

export default App;
