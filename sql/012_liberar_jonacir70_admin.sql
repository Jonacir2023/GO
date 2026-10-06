-- Liberar jonacir70@icloud.com como administrador nas DUAS obras
-- Aplicar em Obra 1 (ivssgstckfcuiyetxdze) e Obra 2 (lwjbuzubnxnzkofcrhah)
-- Data: 06/10/2026

-- Conferir status atual
SELECT id, email, papel FROM auth_usuarios WHERE email = 'jonacir70@icloud.com';

-- Atualizar papel para 'admin'
UPDATE auth_usuarios
SET papel = 'admin'
WHERE email = 'jonacir70@icloud.com';

-- Confirmar mudança
SELECT id, email, papel FROM auth_usuarios WHERE email = 'jonacir70@icloud.com';
