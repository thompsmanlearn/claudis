-- create_place.luau
-- Minimal Roblox place file creator using Lune v0.10.4
-- Creates a DataModel with a Workspace containing a Baseplate and a SpawnLocation
-- Output: minimal_place.rbxl (binary format, publishable via Open Cloud API)

local roblox = require("@lune/roblox")
local fs = require("@lune/fs")

print("Creating minimal Roblox place...")

-- Create the root DataModel
local game = roblox.Instance.new("DataModel")

-- Workspace
local workspace = roblox.Instance.new("Workspace")
workspace.Parent = game

-- Baseplate
local baseplate = roblox.Instance.new("Part")
baseplate.Name = "Baseplate"
baseplate.Anchored = true
baseplate.Size = roblox.Vector3.new(512, 20, 512)
baseplate.Position = roblox.Vector3.new(0, -10, 0)
baseplate.Color = roblox.Color3.fromRGB(106, 127, 63)  -- classic baseplate green
-- Material uses roblox.Enum in Lune (Enum global not available)
baseplate.Material = roblox.Enum.Material.SmoothPlastic
baseplate.Parent = workspace

-- SpawnLocation
local spawn = roblox.Instance.new("SpawnLocation")
spawn.Name = "SpawnLocation"
spawn.Position = roblox.Vector3.new(0, 10, 0)
spawn.Size = roblox.Vector3.new(6, 1, 6)
spawn.Anchored = true
spawn.Parent = workspace

-- Lighting (required for valid place)
local lighting = roblox.Instance.new("Lighting")
lighting.Parent = game

-- ReplicatedStorage
local replicated = roblox.Instance.new("ReplicatedStorage")
replicated.Parent = game

-- StarterPlayer
local starterPlayer = roblox.Instance.new("StarterPlayer")
starterPlayer.Parent = game

-- Serialize to binary .rbxl format
print("Serializing to .rbxl...")
local encoded = roblox.serializePlace(game)

local outputPath = "minimal_place.rbxl"
fs.writeFile(outputPath, encoded)

local fileSize = #encoded
print(string.format("✓ Created %s (%d bytes / %.1f KB)", outputPath, fileSize, fileSize / 1024))
print("Pipeline: Lune Luau → .rbxl → Open Cloud API → Roblox")
