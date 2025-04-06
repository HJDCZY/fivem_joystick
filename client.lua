local joystickData = {
    axes = {},
    buttons = {}
}

-- 注册一个joystick命令用于重新连接
RegisterCommand('joystick', function(source, args, rawCommand)
    TriggerEvent('joystick:reconnect')
end, false)

-- 注册NUI回调,只用于更新数据
RegisterNUICallback('joystickUpdate', function(data, cb)
    joystickData = data
    cb('ok')
end)

RegisterNUICallback('executeCommand', function(data, cb)
    ExecuteCommand(data.command)
    cb('ok')
end)

-- 创建处理线程
Citizen.CreateThread(function()
    while true do
        -- 处理摇杆数据
        local ped = PlayerPedId()
        -- print (joystickData.axes[1])
        if joystickData.axes[1] ~= nil then
            if IsPedInAnyPlane(ped) or IsPedInAnyHeli(ped) then
                -- local plane = GetVehiclePedIsIn(ped, false)
                -- 设置飞机控制
                -- 如果是1或者-1，自动变成1.0的浮点数

                if joystickData.axes[1] == 1 then
                    SetControlNormal(2, 107, 1.0)
                elseif joystickData.axes[1] == -1 then
                    SetControlNormal(2, 107, -1.0)
                else
                    SetControlNormal(2, 107, joystickData.axes[1])
                end
                if joystickData.axes[2] == 1 then
                    SetControlNormal(2, 110, 1.0)
                elseif joystickData.axes[2] == -1 then
                    SetControlNormal(2, 110, -1.0)
                else
                    SetControlNormal(2, 110, joystickData.axes[2])
                end

                if joystickData.axes[3] ~= nil then
                    if joystickData.axes[3] > 0 and joystickData.axes[3] ~= 1 then
                        SetControlNormal(2, 90, joystickData.axes[3])
                    elseif joystickData.axes[3] == 1 then
                        SetControlNormal(2, 90, 1.0)
                    elseif joystickData.axes[3] < 0 and joystickData.axes[3] ~= -1 then
                        SetControlNormal(2, 89, joystickData.axes[3])
                    elseif joystickData.axes[3] == -1 then
                        SetControlNormal(2, 89, -1.0)
                    end
                end

                -- print (joystickData.axes[4])
                -- 首先把-1到1的值转换成0到1的值

                if joystickData.axes[4] ~= nil then
                    -- joystickData.axes[4] = (joystickData.axes[4] + 1) / 2
                    -- print (joystickData.axes[4])
                    -- print (joystickData.axes[4])
                    if joystickData.axes[4] ==0 then
                        SetControlNormal(2, 87, 0.0)
                    elseif joystickData.axes[4] == 1 then
                        SetControlNormal(2, 87, 1.0)
                    -- else
                    --     SetControlNormal(2, 87, joystickData.axes[4])
                    -- end

                    elseif joystickData.axes[4] > 0 and joystickData.axes[4] ~= 1 then
                        SetControlNormal(2, 87, joystickData.axes[4])
                    elseif joystickData.axes[4] < 0 and joystickData.axes[4] ~= -1 then
                        SetControlNormal(2, 88, -joystickData.axes[4])
                    elseif joystickData.axes[4] == -1 then
                        SetControlNormal(2, 88, 1.0)
                    end

                end

            -- elseif IsPedInAnyHeli(ped) then

            end
                
        end
        
        -- 每帧等待
        Citizen.Wait(0)
    end
end)