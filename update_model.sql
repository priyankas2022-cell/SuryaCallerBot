UPDATE user_configurations SET configuration = jsonb_set(configuration::jsonb, '{llm,model}'::text[], '"llama-3.1-8b-instant"'::jsonb) WHERE user_id = 1;
