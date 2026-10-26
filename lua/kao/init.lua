local M = {}

-- default to this repo's launcher so the plugin works without kao on PATH
local root = vim.fn.fnamemodify(debug.getinfo(1, "S").source:sub(2), ":p:h:h:h")
M.config = { cmd = { root .. "/bin/kao" }, width = 60, height = 12 }

local state = {}
local ns = vim.api.nvim_create_namespace("kao")

function M.setup(opts)
  M.config = vim.tbl_deep_extend("force", M.config, opts or {})
  return M
end

local function close()
  local s = state
  state = {}
  for _, win in ipairs({ s.prompt_win, s.results_win }) do
    if win and vim.api.nvim_win_is_valid(win) then
      vim.api.nvim_win_close(win, true)
    end
  end
  if s.job then
    pcall(function() s.job:write(nil) end)
  end
  if s.orig_win and vim.api.nvim_win_is_valid(s.orig_win) then
    vim.api.nvim_set_current_win(s.orig_win)
  end
  if s.orig_mode ~= "i" then
    vim.cmd.stopinsert()
  end
end

local function insert_text(text)
  local s = state
  close()
  if not (s.orig_win and vim.api.nvim_win_is_valid(s.orig_win)) then
    return
  end
  if not vim.bo[s.orig_buf].modifiable then
    -- dashboards, explorers, help: nothing to insert into, so hand the face over as a register
    vim.fn.setreg('"', text)
    pcall(vim.fn.setreg, "+", text)
    vim.notify("kao: buffer is not modifiable; " .. text .. " copied to registers \" and +", vim.log.levels.WARN)
    return
  end
  local row, col = unpack(s.orig_cursor)
  -- normal mode inserts after the cursor char, like `a`
  if s.orig_mode ~= "i" and #vim.api.nvim_buf_get_lines(s.orig_buf, row - 1, row, false)[1] > 0 then
    col = col + #vim.fn.matchstr(vim.api.nvim_buf_get_lines(s.orig_buf, row - 1, row, false)[1]:sub(col + 1), ".")
  end
  vim.api.nvim_buf_set_text(s.orig_buf, row - 1, col, row - 1, col, { text })
  vim.api.nvim_win_set_cursor(s.orig_win, { row, col + #text })
end

local function render()
  if not (state.results_buf and vim.api.nvim_buf_is_valid(state.results_buf)) then
    return
  end
  local lines = {}
  local widest = 0
  for _, item in ipairs(state.results) do
    widest = math.max(widest, vim.fn.strdisplaywidth(item.text))
  end
  widest = math.min(widest, math.floor(M.config.width / 2))
  for _, item in ipairs(state.results) do
    local pad = math.max(widest - vim.fn.strdisplaywidth(item.text), 0)
    table.insert(lines, item.text .. string.rep(" ", pad + 2) .. table.concat(item.tags or {}, " "))
  end
  if #lines == 0 then
    lines = { "  no matches" }
  end
  vim.api.nvim_buf_set_lines(state.results_buf, 0, -1, false, lines)
  vim.api.nvim_buf_clear_namespace(state.results_buf, ns, 0, -1)
  if #state.results > 0 then
    state.sel = math.max(1, math.min(state.sel, #state.results))
    vim.api.nvim_buf_set_extmark(state.results_buf, ns, state.sel - 1, 0, { line_hl_group = "Visual" })
    vim.api.nvim_win_set_cursor(state.results_win, { state.sel, 0 })
  end
end

local function move(delta)
  if #state.results > 0 then
    state.sel = math.max(1, math.min(state.sel + delta, #state.results))
    render()
  end
end

local function jump(index)
  if #state.results > 0 then
    state.sel = index < 0 and #state.results or index
    render()
  end
end

local function send_query()
  local line = vim.api.nvim_buf_get_lines(state.prompt_buf, 0, 1, false)[1] or ""
  state.sel = 1
  pcall(function() state.job:write(line .. "\n") end)
end

function M.open()
  if state.job then
    close()
  end
  local mode = vim.api.nvim_get_mode().mode:sub(1, 1)
  state = {
    results = {},
    sel = 1,
    pending = "",
    orig_win = vim.api.nvim_get_current_win(),
    orig_buf = vim.api.nvim_get_current_buf(),
    orig_cursor = vim.api.nvim_win_get_cursor(0),
    orig_mode = mode,
  }

  local ok, job = pcall(vim.system, vim.list_extend(vim.deepcopy(M.config.cmd), { "--serve" }), {
    stdin = true,
    text = true,
    stdout = function(_, data)
      if not data then
        return
      end
      vim.schedule(function()
        if not state.pending then
          return
        end
        state.pending = state.pending .. data
        for line in state.pending:gmatch("([^\n]*)\n") do
          local okj, decoded = pcall(vim.json.decode, line)
          if okj and type(decoded) == "table" then
            state.results = decoded
          end
        end
        state.pending = state.pending:match("[^\n]*$")
        render()
      end)
    end,
  })
  if not ok then
    state = {}
    vim.notify("kao: cannot start " .. M.config.cmd[1] .. ": " .. tostring(job), vim.log.levels.ERROR)
    return
  end
  state.job = job

  local width, height = M.config.width, M.config.height
  local row = math.max(math.floor((vim.o.lines - height - 4) / 2), 0)
  local col = math.max(math.floor((vim.o.columns - width) / 2), 0)
  state.prompt_buf = vim.api.nvim_create_buf(false, true)
  state.results_buf = vim.api.nvim_create_buf(false, true)
  state.results_win = vim.api.nvim_open_win(state.results_buf, false, {
    relative = "editor", width = width, height = height, row = row + 3, col = col,
    style = "minimal", border = "rounded", focusable = false,
  })
  state.prompt_win = vim.api.nvim_open_win(state.prompt_buf, true, {
    relative = "editor", width = width, height = 1, row = row, col = col,
    style = "minimal", border = "rounded", title = " kao ", title_pos = "center",
  })

  local buf = state.prompt_buf
  vim.api.nvim_create_autocmd({ "TextChangedI", "TextChanged" }, { buffer = buf, callback = send_query })
  vim.api.nvim_create_autocmd({ "BufLeave", "WinClosed" }, { buffer = buf, once = true, callback = function()
    vim.schedule(function() if state.prompt_buf == buf then close() end end)
  end })

  local function accept()
    local item = state.results[state.sel]
    if item then
      insert_text(item.text)
    end
  end
  local map = function(modes, lhs, fn) vim.keymap.set(modes, lhs, fn, { buffer = buf, nowait = true }) end
  -- insert mode edits the query; <Esc> falls through to normal mode in the prompt
  map({ "i", "n" }, "<CR>", accept)
  map({ "i", "n" }, "<C-c>", close)
  map({ "i", "n" }, "<Down>", function() move(1) end)
  map({ "i", "n" }, "<Up>", function() move(-1) end)
  for _, lhs in ipairs({ "<C-n>", "<C-j>" }) do map("i", lhs, function() move(1) end) end
  for _, lhs in ipairs({ "<C-p>", "<C-k>" }) do map("i", lhs, function() move(-1) end) end
  map("n", "j", function() move(1) end)
  map("n", "k", function() move(-1) end)
  map("n", "gg", function() jump(1) end)
  map("n", "G", function() jump(-1) end)
  map("n", "q", close)
  map("n", "<Esc>", close)

  vim.cmd.startinsert()
  send_query()
end

return M
