-- Headless Neovim picker check. Run from the repo root:
--   nvim --headless -u NONE --cmd 'set rtp+=.' -c 'runtime plugin/kao.lua' -c 'luafile tools/nvim_check.lua'
-- Exits 0 when every step passes, 1 otherwise.
-- startinsert only applies after a script returns, so the query is set directly and keys run in normal mode.
local failures = 0
local function check(name, ok, got)
  print(("%s %s%s"):format(ok and "ok  " or "FAIL", name, ok and "" or ("  (got " .. vim.inspect(got) .. ")")))
  if not ok then failures = failures + 1 end
end
local function wait(ms) vim.wait(ms, function() return false end) end
local function keys(k) vim.api.nvim_feedkeys(vim.api.nvim_replace_termcodes(k, true, false, true), "xt", false) end
local function results_win()
  for _, win in ipairs(vim.api.nvim_list_wins()) do
    local c = vim.api.nvim_win_get_config(win)
    if c.relative ~= "" and not c.focusable then return win end
  end
end

vim.api.nvim_buf_set_lines(0, 0, -1, false, { "ab" })
vim.cmd("Kao")
wait(800)
local rw = results_win()
check("results float opened", rw ~= nil, rw)
if rw then
  local initial = vim.api.nvim_buf_get_lines(vim.api.nvim_win_get_buf(rw), 0, -1, false)
  check("initial results shown", #initial > 1, #initial)

  vim.api.nvim_buf_set_lines(0, 0, -1, false, { "cat" })
  vim.api.nvim_exec_autocmds("TextChangedI", { buffer = 0 })
  wait(500)
  local filtered = vim.api.nvim_buf_get_lines(vim.api.nvim_win_get_buf(rw), 0, -1, false)
  -- with a big local dataset both lists hit the 50-result limit, so compare contents, not counts
  check("query changes results", #filtered > 1 and filtered[1] ~= initial[1], filtered[1])

  keys("G")
  check("G goes to last", vim.api.nvim_win_get_cursor(rw)[1] == #filtered, vim.api.nvim_win_get_cursor(rw)[1])
  keys("gg")
  check("gg goes to first", vim.api.nvim_win_get_cursor(rw)[1] == 1, vim.api.nvim_win_get_cursor(rw)[1])
  keys("j")
  check("j moves down", vim.api.nvim_win_get_cursor(rw)[1] == 2, vim.api.nvim_win_get_cursor(rw)[1])
  keys("<CR>")
  wait(200)
  local line = vim.api.nvim_buf_get_lines(0, 0, 1, false)[1]
  check("accept inserts after cursor char", line ~= "ab" and line:sub(1, 1) == "a" and line:sub(-1) == "b", line)
  check("picker closed", #vim.api.nvim_list_wins() == 1, #vim.api.nvim_list_wins())
  check("back in normal mode", vim.api.nvim_get_mode().mode == "n", vim.api.nvim_get_mode().mode)
end

vim.cmd("Kao")
wait(500)
keys("q")
wait(100)
check("q closes", #vim.api.nvim_list_wins() == 1, #vim.api.nvim_list_wins())

vim.cmd((failures == 0) and "qa!" or "cquit 1")
