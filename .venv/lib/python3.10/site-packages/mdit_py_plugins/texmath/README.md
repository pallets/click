[![License](https://img.shields.io/github/license/goessner/markdown-it-texmath.svg)](https://github.com/goessner/markdown-it-texmath/blob/master/licence.txt)
[![npm](https://img.shields.io/npm/v/markdown-it-texmath.svg)](https://www.npmjs.com/package/markdown-it-texmath)
[![npm](https://img.shields.io/npm/dt/markdown-it-texmath.svg)](https://www.npmjs.com/package/markdown-it-texmath)

# markdown-it-texmath

Add TeX math equations to your Markdown documents rendered by [markdown-it](https://github.com/markdown-it/markdown-it) parser. [KaTeX](https://github.com/Khan/KaTeX) is used as a fast math renderer.

## Features
Simplify the process of authoring markdown documents containing math formulas.
This extension is a comfortable tool for scientists, engineers and students with markdown as their first choice document format.

* Macro support
* Simple formula numbering
* Inline math with tables, lists and blockquote.
* User setting delimiters:
  * `'dollars'` (default)
    * inline: `$...$`
    * display: `$$...$$`
    * display + equation number: `$$...$$ (1)`
  * `'brackets'`
    * inline: `\(...\)`
    * display: `\[...\]`
    * display + equation number: `\[...\] (1)`
  * `'gitlab'`
    * inline: ``$`...`$``
    * display: `` ```math ... ``` ``
    * display + equation number: `` ```math ... ``` (1)``
  * `'julia'`
    * inline: `$...$`  or ``` ``...`` ```
    * display: `` ```math ... ``` ``
    * display + equation number: `` ```math ... ``` (1)``
  * `'kramdown'`
    * inline: ``$$...$$``
    * display: `$$...$$`
    * display + equation number: `$$...$$ (1)`

## Show me

View a [test table](https://goessner.github.io/markdown-it-texmath/index.html).

[try it out ...](https://goessner.github.io/markdown-it-texmath/markdown-it-texmath-demo.html)

## Use with `node.js`

Install the extension. Verify having `markdown-it` and `katex` already installed .
```
npm install markdown-it-texmath
```
Use it with JavaScript.
```js
let kt = require('katex'),
    tm = require('markdown-it-texmath').use(kt),
    md = require('markdown-it')().use(tm,{delimiters:'dollars',macros:{"\\RR": "\\mathbb{R}"}});

md.render('Euler\'s identity \(e^{i\pi}+1=0\) is a beautiful formula in $\\RR 2$.')
```

## Use in Browser
```html
<html>
<head>
  <meta charset='utf-8'>
  <link rel="stylesheet" href="katex.min.css">
  <link rel="stylesheet" href="texmath.css">
  <script src="markdown-it.min.js"></script>
  <script src="katex.min.js"></script>
  <script src="texmath.js"></script>
</head>
<body>
  <div id="out"></div>
  <script>
    let md;
    document.addEventListener("DOMContentLoaded", () => {
        const tm = texmath.use(katex);
        md = markdownit().use(tm,{delimiters:'dollars',macros:{"\\RR": "\\mathbb{R}"}});
        out.innerHTML = md.render('Euler\'s identity $e^{i\pi}+1=0$ is a beautiful formula in //RR 2.');
    })
  </script>
</body>
</html>
```
## CDN

Use following links for `texmath.js` and `texmath.css`
* `https://gitcdn.xyz/cdn/goessner/markdown-it-texmath/master/texmath.js`
* `https://gitcdn.xyz/cdn/goessner/markdown-it-texmath/master/texmath.css`

## Dependencies

* [`markdown-it`](https://github.com/markdown-it/markdown-it): Markdown parser done right. Fast and easy to extend.
* [`katex`](https://github.com/Khan/KaTeX): This is where credits for fast rendering TeX math in HTML go to.

## ToDo

 nothing yet

## FAQ

* __`markdown-it-texmath` with React Native does not work, why ?__
  * `markdown-it-texmath` is using regular expressions with `y` [(sticky) property](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/RegExp/sticky) and cannot avoid this. The use of the `y` flag in regular expressions means the plugin is not compatible with React Native (which as of now doesn't support it and throws an error `Invalid flags supplied to RegExp constructor`).

## CHANGELOG

###  [0.6.0] on October 04, 2019
* Add support for [Julia Markdown](https://docs.julialang.org/en/v1/stdlib/Markdown/) on [request](https://github.com/goessner/markdown-it-texmath/issues/15).

###  [0.5.5] on February 07, 2019
* Remove [rendering bug with brackets delimiters](https://github.com/goessner/markdown-it-texmath/issues/9).

###  [0.5.4] on January 20, 2019
* Remove pathological [bug within blockquotes](https://github.com/goessner/mdmath/issues/50).

###  [0.5.3] on November 11, 2018
* Add support for Tex macros (https://katex.org/docs/supported.html#macros) .
* Bug with [brackets delimiters](https://github.com/goessner/markdown-it-texmath/issues/9) .

###  [0.5.2] on September 07, 2018
* Add support for [Kramdown](https://kramdown.gettalong.org/) .

###  [0.5.0] on August 15, 2018
* Fatal blockquote bug investigated. Implemented workaround to vscode bug, which has finally gone with vscode 1.26.0 .

###  [0.4.6] on January 05, 2018
* Escaped underscore bug removed.

###  [0.4.5] on November 06, 2017
* Backslash bug removed.

###  [0.4.4] on September 27, 2017
* Modifying the `block` mode regular expression with `gitlab` delimiters, so removing the `newline` bug.

## License

`markdown-it-texmath` is licensed under the [MIT License](./license.txt)

 © [Stefan Gössner](https://github.com/goessner)
