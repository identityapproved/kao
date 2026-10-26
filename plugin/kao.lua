vim.api.nvim_create_user_command("Kao", function()
  require("kao").open()
end, {})
