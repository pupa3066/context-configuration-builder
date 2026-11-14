# Repository context: Textualize/rich

Source: snapshot at commit fc41075a3206.

## Tests

Tests live in `tests/` (63 test files).

Pytest settings from the repository's own config:

```
pyproject.toml [tool.pytest.ini_options]
  testpaths = ["tests"]
```

## Package layout

- `rich/__init__.py`: Rich text and beautiful formatting in the terminal. Defines get_console, reconfigure, print, print_json, inspect.
- `rich/__main__.py` Defines ColorBox, make_test_card.
- `rich/_emoji_codes.py`
- `rich/_emoji_replace.py`
- `rich/_export_format.py`
- `rich/_extension.py` Defines load_ipython_extension.
- `rich/_fileno.py` Defines get_fileno.
- `rich/_inspect.py` Defines Inspect, get_object_types_mro, get_object_types_mro_as_strings, is_object_one_of_types.
- `rich/_log_render.py` Defines LogRender.
- `rich/_loop.py` Defines loop_first, loop_last, loop_first_last.
- `rich/_null_file.py` Defines NullFile.
- `rich/_palettes.py`
- `rich/_pick.py` Defines pick_bool.
- `rich/_ratio.py` Defines Edge, ratio_resolve, ratio_reduce, ratio_distribute.
- `rich/_spinners.py`: Spinners are from:
- `rich/_stack.py` Defines Stack.
- `rich/_timer.py`: Timer context manager, only used in debug. Defines timer.
- `rich/_win32_console.py`: Light wrapper around the Win32 Console API - this module should only be imported on Windows Defines LegacyWindowsError, WindowsCoordinates, CONSOLE_SCREEN_BUFFER_INFO, CONSOLE_CURSOR_INFO, GetStdHandle, GetConsoleMode, FillConsoleOutputCharacter, FillConsoleOutputAttribute, and 7 more.
- `rich/_windows.py` Defines WindowsConsoleFeatures.
- `rich/_windows_renderer.py` Defines legacy_windows_render.
- `rich/_wrap.py` Defines words, divide_line.
- `rich/abc.py` Defines RichRenderable.
- `rich/align.py` Defines Align, VerticalCenter.
- `rich/ansi.py` Defines AnsiDecoder.
- `rich/bar.py` Defines Bar.
- `rich/box.py` Defines Box.
- `rich/cells.py` Defines CellTable, get_character_cell_size, cached_cell_len, cell_len, split_graphemes, split_text, set_cell_size, chop_cells.
- `rich/color.py` Defines ColorSystem, ColorType, ColorParseError, Color, parse_rgb_hex, blend_rgb.
- `rich/color_triplet.py` Defines ColorTriplet.
- `rich/columns.py` Defines Columns.
- `rich/console.py` Defines NoChange, ConsoleDimensions, ConsoleOptions, RichCast, ConsoleRenderable, CaptureError, NewLine, ScreenUpdate, and 11 more.
- `rich/constrain.py` Defines Constrain.
- `rich/containers.py` Defines Renderables, Lines.
- `rich/control.py` Defines Control, strip_control_codes, escape_control_codes.
- `rich/default_styles.py`
- `rich/diagnose.py` Defines report.
- `rich/emoji.py` Defines NoEmoji, Emoji.
- `rich/errors.py` Defines ConsoleError, StyleError, StyleSyntaxError, MissingStyle, StyleStackError, NotRenderableError, MarkupError, LiveError, and 1 more.
- `rich/file_proxy.py` Defines FileProxy.
- `rich/filesize.py`: Functions for reporting filesizes. Borrowed from https://github.com/PyFilesystem/pyfilesystem2 Defines pick_unit_and_suffix, decimal.
- `rich/highlighter.py` Defines Highlighter, NullHighlighter, RegexHighlighter, ReprHighlighter, JSONHighlighter, ISO8601Highlighter.
- `rich/json.py` Defines JSON.
- `rich/jupyter.py` Defines JupyterRenderable, JupyterMixin, display, print.
- `rich/layout.py` Defines LayoutRender, LayoutError, NoSplitter, Splitter, RowSplitter, ColumnSplitter, Layout.
- `rich/live.py` Defines Live.
- `rich/live_render.py` Defines LiveRender.
- `rich/logging.py` Defines RichHandler.
- `rich/markdown.py` Defines MarkdownElement, UnknownElement, TextElement, Paragraph, HeadingFormat, Heading, CodeBlock, BlockQuote, and 12 more.
- `rich/markup.py` Defines Tag, escape, render.
- `rich/measure.py` Defines Measurement, measure_renderables.
- `rich/padding.py` Defines Padding.
- `rich/pager.py` Defines Pager, SystemPager.
- `rich/palette.py` Defines Palette.
- `rich/panel.py` Defines Panel.
- `rich/pretty.py` Defines install, Pretty, is_expandable, Node, traverse, pretty_repr, pprint.
- `rich/progress.py` Defines track, wrap_file, open, open, open, ProgressColumn, RenderableColumn, SpinnerColumn, and 13 more.
- `rich/progress_bar.py` Defines ProgressBar.
- `rich/prompt.py` Defines PromptError, InvalidResponse, PromptBase, Prompt, IntPrompt, FloatPrompt, Confirm.
- `rich/protocol.py` Defines is_renderable, rich_cast.
- `rich/region.py` Defines Region.
- `rich/repr.py` Defines ReprError, auto, auto, auto, rich_repr, rich_repr, rich_repr.
- `rich/rule.py` Defines Rule.
- `rich/scope.py` Defines render_scope.
- `rich/screen.py` Defines Screen.
- `rich/segment.py` Defines ControlType, Segment, Segments, SegmentLines.
- `rich/spinner.py` Defines Spinner.
- `rich/status.py` Defines Status.
- `rich/style.py` Defines Style, StyleStack.
- `rich/styled.py` Defines Styled.
- `rich/syntax.py` Defines SyntaxTheme, PygmentsSyntaxTheme, ANSISyntaxTheme, PaddingProperty, Syntax.
- `rich/table.py` Defines Column, Row, Table.
- `rich/terminal_theme.py` Defines TerminalTheme.
- `rich/text.py` Defines Span, Text.
- `rich/theme.py` Defines Theme, ThemeStackError, ThemeStack.
- `rich/themes.py`
- `rich/traceback.py` Defines install, Frame, Stack, Trace, PathHighlighter, Traceback.
- `rich/tree.py` Defines Tree.
- `rich/_unicode_data/__init__.py` Defines load.
- `rich/_unicode_data/_versions.py`
- `rich/_unicode_data/unicode10-0-0.py`
- `rich/_unicode_data/unicode11-0-0.py`
- `rich/_unicode_data/unicode12-0-0.py`
- `rich/_unicode_data/unicode12-1-0.py`
- `rich/_unicode_data/unicode13-0-0.py`
- `rich/_unicode_data/unicode14-0-0.py`
- `rich/_unicode_data/unicode15-0-0.py`
- `rich/_unicode_data/unicode15-1-0.py`
- `rich/_unicode_data/unicode16-0-0.py`
- `rich/_unicode_data/unicode17-0-0.py`
- `rich/_unicode_data/unicode4-1-0.py`
- `rich/_unicode_data/unicode5-0-0.py`
- `rich/_unicode_data/unicode5-1-0.py`
- `rich/_unicode_data/unicode5-2-0.py`
- `rich/_unicode_data/unicode6-0-0.py`
- `rich/_unicode_data/unicode6-1-0.py`
- `rich/_unicode_data/unicode6-2-0.py`
- `rich/_unicode_data/unicode6-3-0.py`
- `rich/_unicode_data/unicode7-0-0.py`
- `rich/_unicode_data/unicode8-0-0.py`
- `rich/_unicode_data/unicode9-0-0.py`
