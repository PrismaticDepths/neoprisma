local allow = {
	[0] = true,
	[1] = true,
	[2] = true,
	[13] = true
}

local convert = {
	[0] = 123,
	[2] = 124,
	[1] = 125,
	[13] = 126
}

Neoprisma.Keyboard.onKeyPress.connect(function(vk)
	if allow[vk] then
		Neoprisma.Keyboard.keyStatus(convert[vk],true)
	end
end)

Neoprisma.Keyboard.onKeyRelease.connect(function(vk)
	if allow[vk] then
		Neoprisma.Keyboard.keyStatus(convert[vk],false)
	end
end)