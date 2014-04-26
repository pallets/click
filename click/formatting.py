import textwrap


class TextWrapper(textwrap.TextWrapper):

    def _cutdown(self, ucstr, space_left):
        l = 0
        for i in xrange(len(ucstr)):
            l += len(ucstr[i])
            if space_left < l:
                return (ucstr[:i], ucstr[i:])
        return ucstr, ''

    def _handle_long_word(self, reversed_chunks, cur_line, cur_len, width):
        space_left = max(width - cur_len, 1)

        if self.break_long_words:
            cut, res = self._cutdown(reversed_chunks[-1], space_left)
            cur_line.append(cut)
            reversed_chunks[-1] = res
        elif not cur_line:
            cur_line.append(reversed_chunks.pop())

    def fill_paragraphs(self, text):
        # Remove unnecessary newlines so that we can fill properly
        p = []
        buf = []
        for line in text.splitlines():
            if not line:
                p.append(' '.join(buf))
                buf = []
            else:
                buf.append(line)
        if buf:
            p.append(' '.join(buf))

        rv = []
        for text in p:
            rv.append(self.fill(text))
        return '\n\n'.join(rv)
