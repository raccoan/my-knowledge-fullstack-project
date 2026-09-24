import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'

import 'highlight.js/styles/github.css'

const md:any = new MarkdownIt({
  html: false,

  breaks: true,

  highlight(
    code,
    language,
  ) {
    if (
      language &&
      hljs.getLanguage(language)
    ) {
      try {
        return (
          '<pre><code class="hljs">' +
          hljs.highlight(
            code,
            {
              language,
            },
          ).value +
          '</code></pre>'
        )
      } catch {
        // 高亮失败时使用普通代码
      }
    }

    return (
      '<pre><code>' +
      md.utils.escapeHtml(code) +
      '</code></pre>'
    )
  },
})

export function renderMarkdown(
  content: string,
) {
  return md.render(content)
}